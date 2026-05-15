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

async def ensure_initialized():
    global application, handlers
    if application is None:
        logger.info("[Init] 正在初始化系統組件 (採用分析師專案結構)...")
        
        # 初始化 Telegram Application
        # 注意：我們不需要傳入 Orchestrator 了，直接在 Handlers 裡調用 Client
        application = Application.builder().token(config.TELEGRAM_TOKEN).build()
        handlers = TelegramCommandHandler(gemini_client)
        
        # 註冊處理邏輯 (模仿 Adapter 的行為)
        from telegram.ext import CommandHandler, MessageHandler, filters
        application.add_handler(CommandHandler("start", handlers.handle_start))
        application.add_handler(CommandHandler("research", handlers.handle_research))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        application.add_handler(MessageHandler(filters.COMMAND, handlers.handle_message))
        
        await application.initialize()
        await application.start()
        
        # 設定 Webhook (確保路徑正確)
        if config.WEBHOOK_URL:
            webhook_full_url = f"{config.WEBHOOK_URL}/telegram"
            logger.info(f"[Init] 設定 Webhook: {webhook_full_url}")
            await application.bot.set_webhook(url=webhook_full_url, drop_pending_updates=True)
            
        logger.info("[Init] 初始化完成。")

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    """處理來自 Telegram 的 Webhook 請求"""
    try:
        data = request.get_json(force=True)
        # 每個請求建立獨立 loop，避免 Cloud Run 環境併發衝突
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 確保系統已初始化
        loop.run_until_complete(ensure_initialized())
        
        # 封裝 Update 並處理
        update = Update.de_json(data, application.bot)
        loop.run_until_complete(application.process_update(update))
        
        return 'ok', 200
    except Exception as e:
        logger.error(f"[Webhook] 處理失敗: {e}", exc_info=True)
        return 'error', 500
    finally:
        if 'loop' in locals():
            loop.close()

@app.route('/', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return 'Gemma Assistant is running', 200

if __name__ == '__main__':
    # 啟動 Flask
    logger.info(f"🚀 啟動 Gemma 助理服務，Port: {config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT)
