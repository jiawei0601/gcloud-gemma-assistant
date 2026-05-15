import asyncio
import logging
import os
import http.server
import threading
import sys
import json
from dotenv import load_dotenv

# 強制刷新 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
load_dotenv()

# 配置全局日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("Main")

# 全域組件
tg_adapter = None
firestore_client = None
update_queue = asyncio.Queue()

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # 健康檢查路徑
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        # Telegram Webhook 進入點
        if self.path == "/telegram":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                update_json = json.loads(post_data.decode('utf-8'))
                
                # 1. 極速放進 Queue
                # 注意：這裡是在 Thread 中運行，所以要用 loop.call_soon_threadsafe 或 run_coroutine_threadsafe
                # 但更簡單的方式是直接在 do_POST 中完成 Ack
                main_loop.call_soon_threadsafe(update_queue.put_nowait, update_json)
                
                # 2. 立即回傳 200 OK 給 Telegram，防止重試
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            except Exception as e:
                logger.error(f"Webhook Error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args): return

async def update_worker():
    """
    背景工作者：從 Queue 取出更新並處理。
    包含 Firestore 去重邏輯。
    """
    logger.info("👷 [Worker] 背景工作者啟動。")
    while True:
        update_json = await update_queue.get()
        update_id = update_json.get("update_id")
        
        if not update_id:
            update_queue.task_done()
            continue

        try:
            # 1. Firestore 原子鎖定
            is_new = await firestore_client.try_lock(update_id)
            
            if is_new:
                logger.info(f"🆕 [Worker] 處理新更新: {update_id}")
                # 2. 處理更新
                if tg_adapter:
                    await tg_adapter.process_update(update_json)
                await firestore_client.mark_completed(update_id)
            else:
                logger.info(f"⏭️ [Worker] 跳過重複更新: {update_id}")
                
        except Exception as e:
            logger.error(f"💥 [Worker] 處理失敗 ({update_id}): {e}", exc_info=True)
            try:
                await firestore_client.mark_failed(update_id, str(e))
            except: pass
        finally:
            update_queue.task_done()

def run_http_server():
    port = int(os.getenv("PORT", "8080"))
    server_address = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(server_address, WebhookHandler)
    logger.info(f"✅ [SYSTEM] Webhook 伺服器啟動於 0.0.0.0:{port}")
    httpd.serve_forever()

async def start_bot():
    global tg_adapter, main_loop, firestore_client
    main_loop = asyncio.get_running_loop()
    
    logger.info("🎬 [SYSTEM] 啟動初始化流程 (Stateless Webhook 模式)...")
    
    try:
        from src.clients.gemini_client import gemini_client
        from src.communication.telegram_adapter import TelegramAdapter
        from src.shared.firestore_client import FirestoreClient
        from config import config
        
        # 初始化 Firestore
        firestore_client = FirestoreClient(project_id=config.PROJECT_ID)
        
        bot_token = config.TELEGRAM_TOKEN
        admin_id = os.getenv("ADMIN_CHAT_ID")
        webhook_url = config.WEBHOOK_URL
        
        if not bot_token:
            logger.error("❌ [BOT] TELEGRAM_BOT_TOKEN 缺失！")
            return

        # 初始化 Telegram Adapter
        tg_adapter = TelegramAdapter(bot_token, gemini_client)
        await tg_adapter.initialize()
        
        # 啟動 Webhook 監聽
        if webhook_url:
            await tg_adapter.run_webhook(webhook_url, config.PORT)
        
        # 啟動背景 Worker
        asyncio.create_task(update_worker())
        
        # 啟動 HTTP Server (處理健康檢查與 Webhook)
        threading.Thread(target=run_http_server, daemon=True).start()
        
        if admin_id:
            await tg_adapter.send_startup_notification(admin_id)
            
        logger.info("💎 [SYSTEM] 系統已就緒，等待任務中。")
        while True:
            await asyncio.sleep(3600)
                
    except Exception as e:
        logger.critical(f"💥 [FATAL] 啟動失敗: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("👋 [SYSTEM] 程式終止。")