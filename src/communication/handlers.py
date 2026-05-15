import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from src.clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class TelegramCommandHandler:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /start 指令"""
        user = update.effective_user
        welcome_text = (
            f"你好 {user.first_name}！👋\n\n"
            "我是基於 **Gemini 3.1 Pro** 的專業研究助理。\n"
            "我已切換至「分析師團隊」的高效架構。\n\n"
            "你可以使用以下指令：\n"
            "🔍 `/research <主題>` - 開始深度研究任務\n"
            "💬 直接對話 - 進行一般性詢問"
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def handle_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /research 指令"""
        if not context.args:
            await update.message.reply_text("請提供研究主題。用法：`/research 川習會`")
            return

        topic = " ".join(context.args)
        status_msg = await update.message.reply_text(f"🔍 正在為您啟動關於『{topic}』的研究任務...\n這可能需要一點時間。")

        # 調用 GeminiClient 進行研究（模擬深度研究流程）
        # 在分析師架構中，我們直接請求模型進行多維度分析
        prompt = f"請擔任資深市場分析師，針對主題『{topic}』進行深度研究。請涵蓋：1. 現況概述 2. 潛在影響 3. 未來展望。請以 Markdown 格式輸出。"
        
        import asyncio
        success, result = await asyncio.to_thread(self.gemini.ask, prompt)

        if success:
            await status_msg.edit_text(result, parse_mode='Markdown')
        else:
            await status_msg.edit_text(f"❌ 抱歉，執行研究時發生錯誤：\n{result}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理一般文字訊息"""
        if not update.message or not update.message.text:
            return

        user_text = update.message.text
        # 如果是群組訊息且沒有提到機器人，則忽略（除非是私訊）
        
        import asyncio
        success, result = await asyncio.to_thread(self.gemini.ask, user_text)
        
        if success:
            await update.message.reply_text(result, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"⚠️ 發生錯誤：{result}")
