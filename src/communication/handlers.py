import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from src.clients.gemini_client import gemini_client

logger = logging.getLogger(__name__)

# --- 研究團隊人設定義 (保持不變) ---
PROMPT_DATA_COLLECTOR = """你是「數據與事實搜集員」。你的任務是搜集最精確、最新的事實。"""
PROMPT_CONTEXT_ANALYST = """你是「背景與脈絡分析師」。你的任務是分析前因後果。"""
PROMPT_IMPACT_ASSESSOR = """你是「趨勢與影響評估師」。你的任務是預測未來影響。"""
PROMPT_CHIEF_EDITOR = """你是「首席研究總監」。你的任務是彙整成最終報告。"""

class TelegramCommandHandler:
    def __init__(self, gemini_client):
        self.gemini = gemini_client

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = "🚀 **專業研究助理已啟動**\n請使用指令 `/research <主題>` 或直接對話。"
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def handle_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("請提供研究主題。")
            return

        topic = " ".join(context.args)
        status_msg = await update.message.reply_text(f"🔍 **啟動專案研究：{topic}**\n正在指派專家團隊...")

        try:
            # 使用 asyncio.to_thread 執行同步的專家調用
            tasks = [
                asyncio.to_thread(self.gemini.ask_expert_sync, PROMPT_DATA_COLLECTOR, f"主題：{topic}"),
                asyncio.to_thread(self.gemini.ask_expert_sync, PROMPT_CONTEXT_ANALYST, f"主題：{topic}"),
                asyncio.to_thread(self.gemini.ask_expert_sync, PROMPT_IMPACT_ASSESSOR, f"主題：{topic}")
            ]
            
            results = await asyncio.gather(*tasks)
            
            cio_input = f"數據：{results[0]['text']}\n背景：{results[1]['text']}\n影響：{results[2]['text']}"
            
            # 由總監進行彙整
            final_res = await asyncio.to_thread(self.gemini.ask_expert_sync, PROMPT_CHIEF_EDITOR, cio_input, use_search=False)
            
            await status_msg.edit_text(final_res['text'], parse_mode='Markdown')

        except Exception as e:
            logger.error(f"研究流程報錯: {e}")
            await update.message.reply_text(f"❌ 發生錯誤：{e}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        user_text = update.message.text
        CHAT_PERSONA = "你是「互動式研究助理」。請具備搜尋能力回答問題。"
        
        # 同樣使用 to_thread 執行
        res = await asyncio.to_thread(self.gemini.ask_expert_sync, CHAT_PERSONA, user_text, use_search=True)
        
        if res.get("success"):
            await update.message.reply_text(res['text'], parse_mode='Markdown')
        else:
            await update.message.reply_text(f"⚠️ 報錯：{res.get('text')}")
