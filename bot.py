import logging
import asyncio
import sys
from flask import Flask, request
from telegram import Update, Bot

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

async def handle_update(data):
    """
    採用與參考專案一致的「無狀態」處理邏輯：
    1. 每個請求建立獨立 Bot 物件
    2. 直接解析 Update
    3. 直接調用 Handlers
    """
    bot = Bot(token=config.TELEGRAM_TOKEN)
    update = Update.de_json(data, bot)
    
    # 初始化處理器
    handlers = TelegramCommandHandler(gemini_client)
    
    # 判斷訊息類型並路由 (模仿 Application 的行為)
    if update.message and update.message.text:
        text = update.message.text
        if text.startswith('/start'):
            await handlers.handle_start(update, None)
        elif text.startswith('/research'):
            # 簡單解析指令參數
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
        # 使用 asyncio.run() 確保每個請求都有獨立且乾淨的 loop
        asyncio.run(handle_update(data))
        return 'ok', 200
    except Exception as e:
        logger.error(f"[Webhook] 處理失敗: {e}", exc_info=True)
        return 'error', 500

@app.route('/', methods=['GET'])
def health_check():
    return 'Gemma Assistant (Stabilized) is active', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT)
