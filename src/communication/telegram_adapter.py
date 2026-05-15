import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.core.orchestrator import Orchestrator
from src.communication.handlers import CommandHandlers

logger = logging.getLogger(__name__)

class TelegramAdapter:
    def __init__(self, token: str, orchestrator: Orchestrator):
        self.application = Application.builder().token(token).build()
        self.orchestrator = orchestrator
        self.handlers = CommandHandlers(orchestrator)
        self._setup_handlers()

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CommandHandler("research", self.handlers.research))
        self.application.add_handler(CommandHandler("status", self.handlers.status))
        self.application.add_handler(MessageHandler(filters.COMMAND, self.handlers.unknown_command))
        # 捕捉所有非指令訊息，提供正確引導
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message))

    async def initialize(self):
        """初始化 Application 物件"""
        await self.application.initialize()

    async def send_startup_notification(self, admin_id: str):
        """發送啟動通知給管理員"""
        try:
            from src.intelligence.factory import IntelligenceFactory
            provider = IntelligenceFactory.create_provider()
            # 這裡我們手動判斷模型名稱，因為 Provider 現在是動態的
            model_info = "Gemini 3.1 Pro"
            
            await self.application.bot.send_message(
                chat_id=admin_id,
                text=f"🤖 **Gemma 4 研究助理已上線 (Webhook 模式)**\n\n當前引擎：`{model_info}`\n機房位置：`Cloud Run (asia-east1)`\n狀態：已準備好執行任務。"
            )
        except Exception as e:
            logger.error(f"發送啟動通知失敗: {e}")

    async def run_webhook(self, url: str, port: int):
        """以 Webhook 模式執行"""
        logger.info(f"🌐 [WEBHOOK] 設定網鉤至: {url}")
        
        # 建立更新隊列與應用程式啟動
        await self.application.start()
        await self.application.bot.set_webhook(url=f"{url}/telegram", drop_pending_updates=True)
        
        # 這裡不使用 application.run_webhook，因為我們已經有自己的 HTTP Server (main.py)
        # 我們只需要讓 application 處於 start 狀態即可，由 main.py 將 update 餵進來
        logger.info("✅ [WEBHOOK] 應用程式已進入監聽狀態。")

    async def process_update(self, update_json: dict):
        """處理來自 Webhook 的更新"""
        update = Update.de_json(data=update_json, bot=self.application.bot)
        await self.application.process_update(update)
