import logging
import asyncio
import sys
from flask import Flask, request
from telegram import Update, Bot
from google.cloud import firestore

from config import config
from src.clients.gemini_client import gemini_client
from src.communication.handlers import TelegramCommandHandler

# 強制刷新日誌
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger("BotEntry")

app = Flask(__name__)

def is_duplicate_update(update_id):
    """使用 Firestore 進行訊息去重"""
    try:
        db = firestore.Client(project=config.PROJECT_ID)
        # 在 webhook_locks 集合中建立文件
        doc_ref = db.collection('webhook_locks').document(str(update_id))
        
        # 使用 create()：如果文件已存在會報錯，以此作為分散式鎖
        doc_ref.create({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'status': 'processing'
        })
        return False # 成功建立，是第一筆請求
    except Exception as e:
        if "AlreadyExists" in str(e) or "409" in str(e):
            return True # 已存在，是重複請求
        logger.error(f"[Deduplication] 檢查失敗: {e}")
        return False # 資料庫問題時放行，避免服務中斷

async def handle_update(data):
    bot = Bot(token=config.TELEGRAM_TOKEN)
    update = Update.de_json(data, bot)
    
    # 執行去重檢查
    if update.update_id and is_duplicate_update(update.update_id):
        logger.info(f"[Deduplication] 忽略重複請求: {update.update_id}")
        return

    handlers = TelegramCommandHandler(gemini_client)
    
    if update.message and update.message.text:
        text = update.message.text
        if text.startswith('/start'):
            await handlers.handle_start(update, None)
        elif text.startswith('/research'):
            parts = text.split(None, 1)
            class MockContext:
                def __init__(self, args): self.args = args
            context = MockContext(parts[1].split() if len(parts) > 1 else [])
            await handlers.handle_research(update, context)
        else:
            await handlers.handle_message(update, None)

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json(force=True)
        asyncio.run(handle_update(data))
        return 'ok', 200
    except Exception as e:
        logger.error(f"[Webhook] 處理失敗: {e}", exc_info=True)
        return 'ok', 200 # 即使失敗也回傳 200，停止 Telegram 的自動重試

@app.route('/', methods=['GET'])
def health_check():
    return 'Gemma Assistant (Stabilized with Deduplication) is active', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT)
