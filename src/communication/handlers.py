import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from src.clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# --- 研究團隊人設定義 ---
PROMPT_DATA_COLLECTOR = """你是「數據與事實搜集員」。
你的任務是針對使用者提出的主題，搜集最精確、最新的原始數據、事件時間線與關鍵事實。
要求：
1. 僅提供客觀事實，不進行評論。
2. 使用條列式，標註來源。
3. 具備 Google 搜尋能力，確保資訊是 2026 年最新的。"""

PROMPT_CONTEXT_ANALYST = """你是「背景與脈絡分析師」。
你的任務是分析該主題的前因後果、歷史脈絡以及相關利益團體的動機。
要求：
1. 解釋「為什麼」會發生這件事。
2. 指出該議題在當前環境下的重要性。
3. 具備 Google 搜尋能力。"""

PROMPT_IMPACT_ASSESSOR = """你是「趨勢與影響評估師」。
你的任務是分析該主題對未來的潛在影響、風險因素以及可能的發展趨勢。
要求：
1. 提供短、中、長期的影響預測。
2. 指出潛在的風險點或轉折點。
3. 具備 Google 搜尋能力。"""

PROMPT_CHIEF_EDITOR = """你是「首席研究總監」。
你的任務是根據【數據搜集】、【背景脈絡】與【影響評估】三份報告，為客戶撰寫一份最終的「專題研究報告」。
報告格式要求：
1. 使用專業、客觀且具洞察力的繁體中文語氣。
2. 結構包含：[執行摘要]、[詳盡分析]、[未來建議]。
3. 使用 Markdown 格式，包含適當的標題與表格。
4. 在結尾加上免責聲明。"""

class TelegramCommandHandler:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /start 指令"""
        welcome_text = (
            "🚀 **專業研究助理已啟動**\n\n"
            "我已配置了四位 AI 專家為您服務：\n"
            "1. 📊 數據搜集員 (Facts)\n"
            "2. 🏛️ 背景分析師 (Context)\n"
            "3. 🔮 展望評估師 (Impact)\n"
            "4. ✍️ 首席研究總監 (Final Report)\n\n"
            "請使用指令：\n"
            "`/research <您的主題>`\n\n"
            "我將為您產生一份深度彙整報告。"
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def handle_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /research 指令，執行多代理人協作流程"""
        if not context.args:
            await update.message.reply_text("請提供研究主題。例如：`/research 2026年半導體產業趨勢`")
            return

        topic = " ".join(context.args)
        chat_id = update.effective_chat.id
        
        status_msg = await update.message.reply_text(
            f"🔍 **啟動專案研究：{topic}**\n\n"
            "正在指派專家團隊上網搜集資料並進行交叉分析，預計耗時 20-30 秒..."
        )

        try:
            # 1. 併發啟動三位專家的研究任務
            tasks = [
                self.gemini.ask_expert(PROMPT_DATA_COLLECTOR, f"研究主題：{topic}"),
                self.gemini.ask_expert(PROMPT_CONTEXT_ANALYST, f"研究主題：{topic}"),
                self.gemini.ask_expert(PROMPT_IMPACT_ASSESSOR, f"研究主題：{topic}")
            ]
            
            results = await asyncio.gather(*tasks)
            
            # 2. 檢查是否有失敗的任務
            for r in results:
                if not r.get("success"):
                    raise Exception(f"專家調用失敗: {r.get('text')}")

            # 3. 準備總編輯的輸入
            cio_input = (
                f"主題：{topic}\n\n"
                f"【數據搜集報告】\n{results[0]['text']}\n\n"
                f"【背景脈絡報告】\n{results[1]['text']}\n\n"
                f"【影響評估報告】\n{results[2]['text']}"
            )
            
            await status_msg.edit_text(f"✅ 專家報告已彙整，正在由首席總監產出最終報告...")

            # 4. 由總編輯產出最終報告
            final_res = await self.gemini.ask_expert(PROMPT_CHIEF_EDITOR, cio_input, use_search=False)
            
            if not final_res.get("success"):
                raise Exception(f"總監報告失敗: {final_res.get('text')}")

            # 5. 發送最終報告 (考慮到 Telegram 4096 字元限制)
            report_text = final_res['text']
            if len(report_text) > 4000:
                report_text = report_text[:4000] + "...\n\n(由於內容過長，已截斷部分資訊)"

            await status_msg.edit_text(report_text, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"研究流程發生錯誤: {e}", exc_info=True)
            await update.message.reply_text(f"❌ 研究過程發生錯誤：{str(e)}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """一般對話：交由總監直接回應"""
        if not update.message or not update.message.text:
            return
            
        success, result = self.gemini.ask(update.message.text)
        if success:
            await update.message.reply_text(result, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"⚠️ 發生錯誤：{result}")
