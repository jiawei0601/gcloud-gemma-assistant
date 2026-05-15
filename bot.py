import logging
import asyncio
import sys
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application

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

# 全域狀態
application = None
handlers = None

async def setup_application():
    """初始化 Telegram Application (異步)"""
    global application, handlers
    if application is None:
        logger.info("[Init] 正在初始化研究助理系統...")
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()
        handlers = TelegramCommandHandler(gemini_client)
        
        from telegram.ext import CommandHandler, MessageHandler, filters
        application.add_handler(CommandHandler("start", handlers.handle_start))
        application.add_handler(CommandHandler("research", handlers.handle_research))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        application.add_handler(MessageHandler(filters.COMMAND, handlers.handle_message))
        
        await application.initialize()
        await application.start()
        
        if config.WEBHOOK_URL:
            webhook_full_url = f"{config.WEBHOOK_URL}/telegram"
            await application.bot.set_webhook(url=webhook_full_url, drop_pending_updates=True)
            logger.info(f"[Init] Webhook 已註冊: {webhook_full_url}")

async def process_update(data):
    """核心處理流程 (與參考專案一致)"""
    await setup_application()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    """處理來自 Telegram 的 Webhook 請求"""
    try:
        data = request.get_json(force=True)
        # 採用參考專案的穩定模式：直接啟動 asyncio.run
        asyncio.run(process_update(data))
        return 'ok', 200
    except Exception as e:
        logger.error(f"[Webhook] 處理失敗: {e}", exc_info=True)
        return 'error', 500

@app.route('/', methods=['GET'])
def health_check():
    return 'Research Assistant is active', 200

if __name__ == '__main__':
    logger.info(f"🚀 啟動研究助理服務，Port: {config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT)
