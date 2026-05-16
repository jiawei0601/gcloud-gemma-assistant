import os
import logging
import json
import asyncio
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# 強制刷新 stdout
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

load_dotenv()

# 配置全局日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("Bot")

app = Flask(__name__)

# 全域組件
tg_adapter = None
firestore_client = None
update_queue = None
main_loop = None
initialization_event = None

async def update_worker(queue, adapter, firestore):
    """
    背景工作者：從 Queue 取出更新並處理。
    """
    # 等待初始化完成
    logger.info("👷 [Worker] 等待組件初始化完成...")
    await initialization_event.wait()
    logger.info("👷 [Worker] 背景工作者正式啟動。")
    
    while True:
        update_json = await queue.get()
        update_id = update_json.get("update_id")
        
        if not update_id:
            queue.task_done()
            continue

        try:
            # 1. Firestore 原子鎖定 (去重)
            is_new = await firestore.try_lock(update_id)
            
            if is_new:
                logger.info(f"🆕 [Worker] 處理新更新: {update_id}")
                # 2. 處理更新
                if adapter:
                    await adapter.process_update(update_json)
                await firestore.mark_completed(update_id)
            else:
                logger.info(f"⏭️ [Worker] 跳過重複更新: {update_id}")
                
        except Exception as e:
            logger.error(f"💥 [Worker] 處理失敗 ({update_id}): {e}", exc_info=True)
            try:
                await firestore.mark_failed(update_id, str(e))
            except: pass
        finally:
            queue.task_done()


# 初始化組件
def initialize_components():
    global tg_adapter, firestore_client, update_queue, main_loop, initialization_event
    
    from src.clients.gemini_client import gemini_client
    from src.communication.telegram_adapter import TelegramAdapter
    from src.shared.firestore_client import FirestoreClient
    from config import config
    
    # 1. 初始化 Firestore
    firestore_client = FirestoreClient(project_id=config.PROJECT_ID)
    
    # 2. 初始化 Telegram Adapter
    tg_adapter = TelegramAdapter(config.TELEGRAM_TOKEN, gemini_client, firestore_client)
    
    # 3. 建立 Async Loop
    main_loop = asyncio.new_event_loop()
    
    # 4. 啟動背景線程
    def run_loop():
        asyncio.set_event_loop(main_loop)
        
        global update_queue, initialization_event
        update_queue = asyncio.Queue()
        initialization_event = asyncio.Event()
        
        # 啟動 Worker
        main_loop.create_task(update_worker(update_queue, tg_adapter, firestore_client))
        
        # 執行初始化序列
        async def startup_sequence():
            try:
                logger.info("🎬 [SYSTEM] 開始執行初始化序列...")
                await tg_adapter.initialize()
                
                if config.WEBHOOK_URL:
                    await tg_adapter.run_webhook(config.WEBHOOK_URL, config.PORT)
                
                initialization_event.set()
                logger.info("💎 [SYSTEM] 初始化序列完成，Event 已設置。")
            except Exception as e:
                logger.critical(f"💥 [SYSTEM] 初始化失敗: {e}", exc_info=True)

        main_loop.create_task(startup_sequence())
        main_loop.run_forever()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    
    # 等待 Queue 初始化 (極短時間)
    import time
    for _ in range(10):
        if update_queue is not None: break
        time.sleep(0.1)
    
    logger.info("🚀 [SYSTEM] 背景執行緒已啟動。")

# 提醒邏輯
async def send_reminder_to_all():
    """
    發送提醒給所有活躍使用者。
    """
    if not tg_adapter or not firestore_client:
        return
    
    # 確保發送前已初始化
    if initialization_event and not initialization_event.is_set():
        logger.warning("Reminder triggered but system not initialized yet.")
        return

    users = await firestore_client.get_all_active_users()
    for chat_id in users:
        todos = await firestore_client.get_pending_todos(chat_id)
        if todos:
            text = "⏰ **定期待辦事項提醒**\n\n您還有以下未完成事項：\n"
            for i, todo in enumerate(todos, 1):
                text += f"{i}. {todo['task']}\n"
            
            try:
                await tg_adapter.application.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
                logger.info(f"Sent reminder to {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send reminder to {chat_id}: {e}")

# 首次請求時初始化
with app.app_context():
    initialize_components()

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    """
    Telegram Webhook 進入點
    """
    try:
        update_json = request.get_json()
        if update_json and update_queue and main_loop:
            # 極速放入 Queue
            main_loop.call_soon_threadsafe(update_queue.put_nowait, update_json)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Webhook Route Error: {e}")
        return 'Error', 500

@app.route('/remind', methods=['GET'])
def trigger_reminder():
    """
    由 Google Cloud Scheduler 觸發的提醒路徑。
    """
    if main_loop:
        asyncio.run_coroutine_threadsafe(send_reminder_to_all(), main_loop)
        return 'Reminder triggered', 200
    return 'Loop not initialized', 500

@app.route('/', methods=['GET'])
def health_check():
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
