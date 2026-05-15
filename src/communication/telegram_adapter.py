import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from src.communication.handlers import TelegramCommandHandler
from src.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

class TelegramAdapter:
    """Telegram 通訊適配器，負責 Bot 的生命週期與路由"""
    
    def __init__(self, bot_token: str, orchestrator: Orchestrator):
        self.bot_token = bot_token
        self.orchestrator = orchestrator
        self.handler_logic = TelegramCommandHandler(orchestrator)
        self.application = None

    async def initialize(self):
        """初始化 Telegram Application 並註冊處理器"""
        self.application = ApplicationBuilder().token(self.bot_token).build()
        
        # 註冊指令
        self.application.add_handler(CommandHandler("start", self.handler_logic.handle_start))
        self.application.add_handler(CommandHandler("research", self.handler_logic.handle_research))
        
        logger.info("Telegram Adapter 已完成初始化。")

    async def run(self):
        """啟動 Bot"""
        if not self.application:
            await self.initialize()
            
        logger.info("Telegram Bot 正在啟動輪詢...")
        await self.application.run_polling()

    async def send_startup_notification(self, chat_id: str):
        """啟動時發送通知給管理員"""
        if not self.application:
            await self.initialize()
            
        try:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text="🚀 **Gemma AI Research Assistant 已成功部屬並啟動！**\n\n目前正在 Google Cloud Run 上運行，隨時準備為您服務。"
            )
            logger.info(f"已發送啟動通知給管理員: {chat_id}")
        except Exception as e:
            logger.error(f"發送啟動通知失敗: {e}")
