import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

class TelegramCommandHandler:
    """處理 Telegram 指令的邏輯層"""
    
    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /start 指令"""
        await update.message.reply_text(
            "🤖 **Gemma 4 研究助理已上線**\n\n"
            "您可以使用以下指令：\n"
            "/research <主題> - 啟動一項新的研究任務\n"
            "/status - 查詢目前任務狀態\n\n"
            "所有分析均由 Gemma 4 26B 模型驅動。"
        )

    async def handle_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /research <query> 指令"""
        if not context.args:
            await update.message.reply_text("請輸入研究主題，例如：`/research 永續能源的未來`", parse_mode="Markdown")
            return

        query = " ".join(context.args)
        await update.message.reply_text(f"🔍 正在為您啟動關於『{query}』的研究任務...\n這可能需要幾分鐘時間。")
        
        try:
            # 啟動研究任務
            # 注意：在生產環境中，這裡應該是非同步背景任務，以免阻塞 Bot
            result_task = await self.orchestrator.run_research(
                goal=query,
                destination_folder="GoogleDrive:/MyResearch"
            )
            
            # 回傳結果摘要
            if result_task.artifacts:
                report = result_task.artifacts[0]
                await update.message.reply_text(
                    f"✅ **研究完成！**\n\n"
                    f"標題：{report.title}\n\n"
                    f"**摘要回報：**\n{report.content[:1000]}...",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("✅ 研究已完成，但未生成具體報告。")
                
        except Exception as e:
            logger.error(f"研究任務失敗：{e}", exc_info=True)
            await update.message.reply_text(f"❌ 抱歉，執行研究時發生錯誤：{str(e)}")
