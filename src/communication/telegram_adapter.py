import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from src.core.orchestrator import Orchestrator
from src.communication.handlers import TelegramCommandHandler

logger = logging.getLogger(__name__)

class TelegramAdapter:
    def __init__(self, token: str, client: any):
        self.application = Application.builder().token(token).build()
        self.client = client
        self.handlers = TelegramCommandHandler(client)
        self._setup_handlers()

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.handlers.handle_start))
        self.application.add_handler(CommandHandler("research", self.handlers.handle_research))
        self.application.add_handler(CommandHandler("status", self.handlers.handle_start)) # 暫時映射到 start
        # 捕捉所有非指令訊息與未知指令
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message))
        self.application.add_handler(MessageHandler(filters.COMMAND, self.handlers.handle_message))

    async def initialize(self):
        """初始化 Application 物件"""
        await self.application.initialize()

    async def send_startup_notification(self, admin_id: str):
        """發送啟動通知給管理員"""
        try:
            from config import config
            await self.application.bot.send_message(
                chat_id=admin_id,
                text=f"🤖 **Gemma 4 研究助理已上線 (穩定版)**\n\n當前引擎：`{config.GEMINI_MODEL_ID}`\n去重機制：`Firestore Atomic (Enabled)`\n架構模式：`Flask + Async Queue`\n狀態：已準備好執行任務。"
            )
        except Exception as e:
            logger.error(f"發送啟動通知失敗: {e}")

    async def run_webhook(self, url: str, port: int):
        """以 Webhook 模式執行"""
        logger.info(f"🌐 [WEBHOOK] 設定網鉤至: {url}")
        await self.application.start()
        await self.application.bot.set_webhook(url=f"{url}/telegram", drop_pending_updates=True)
        logger.info("✅ [WEBHOOK] 應用程式已進入監聽狀態。")

    async def process_update(self, update_json: dict):
        """處理來自 Webhook 的更新"""
        update = Update.de_json(data=update_json, bot=self.application.bot)
        await self.application.process_update(update)
