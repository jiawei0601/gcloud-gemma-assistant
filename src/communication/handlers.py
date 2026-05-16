import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# --- 研究團隊人設定義 ---
PROMPT_DATA_COLLECTOR = "你是「數據與事實搜集員」。你的任務是搜尋與提供最精確、最新的事實數據。請列出關鍵數據點。"
PROMPT_CONTEXT_ANALYST = "你是「背景與脈絡分析師」。你的任務是分析主題的歷史背景、現狀以及相關的產業脈絡。"
PROMPT_IMPACT_ASSESSOR = "你是「趨勢與影響評估師」。你的任務是根據現有資訊預測未來的可能發展方向與潛在影響。"
PROMPT_CHIEF_EDITOR = "你是「首席研究總監」。你的任務是將各專家的分析結果整合成一份結構完整、專業且具備深度見解的最終報告。請使用 Markdown 格式。"
PROMPT_TASK_EXTRACTOR = """你是一個任務管理助理。請分析使用者的對話內容，判斷其中是否包含「未完成事項」、「待辦任務」或「未來要做的事情」。
如果包含，請將其提取為簡短的任務清單。
格式要求：每個任務一行，僅輸出任務內容。
如果沒有包含任何任務，請回覆「NONE」。"""

class TelegramCommandHandler:
    def __init__(self, gemini_client, firestore_client):
        self.gemini = gemini_client
        self.firestore = firestore_client
        # 限制同時運行的 Agent 數量，避免 API 速率限制
        self.semaphore = asyncio.Semaphore(5)

    async def _safe_send_or_edit(self, message, text, parse_mode='Markdown'):
        """安全地發送或編輯訊息，支援 Markdown 失敗回退"""
        try:
            if hasattr(message, 'edit_text'):
                await message.edit_text(text, parse_mode=parse_mode)
            else:
                await message.reply_text(text, parse_mode=parse_mode)
        except Exception as e:
            if "Can't parse entities" in str(e):
                logger.warning(f"Markdown 解析失敗，切換至純文字發送: {e}")
                if hasattr(message, 'edit_text'):
                    await message.edit_text(text)
                else:
                    await message.reply_text(text)
            elif "Message is not modified" in str(e):
                pass
            else:
                logger.error(f"發送訊息失敗: {e}")

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await self.firestore.save_user_chat(chat_id)
        welcome_text = "🚀 **專業研究助理 (Multi-Agent) 已啟動**\n\n可用指令：\n- `/research <主題>`：啟動深度專案研究\n- `/todos`：查看待辦事項\n- `/health`：系統狀態檢查\n- 直接輸入問題：啟動快速互動查詢"
        await self._safe_send_or_edit(update.message, welcome_text)

    async def handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """檢查系統健康狀態"""
        from config import config
        import time
        
        status_text = "🏥 **系統健康診斷報告**\n\n"
        
        # 1. 檢查 Gemini
        try:
            start_time = time.time()
            res = await self._run_agent_task("你是健康檢查員。請回覆『PONG』。", "PING", use_search=False)
            latency = time.time() - start_time
            if res.get("success"):
                status_text += f"✅ **AI 引擎 (Gemini)**: 在線 (延遲: {latency:.2f}s)\n"
            else:
                status_text += f"❌ **AI 引擎 (Gemini)**: 錯誤 ({res.get('text')})\n"
        except:
            status_text += "❌ **AI 引擎 (Gemini)**: 離線\n"
            
        # 2. 檢查 Firestore
        try:
            users = await self.firestore.get_all_active_users()
            status_text += f"✅ **資料庫 (Firestore)**: 在線 (用戶數: {len(users)})\n"
        except:
            status_text += "❌ **資料庫 (Firestore)**: 錯誤\n"
            
        # 3. 系統資訊
        status_text += f"\n⚙️ **環境資訊**:\n- 引擎: `{config.GEMINI_MODEL_ID}`\n- 地區: `{config.LOCATION}`\n- 版本: `Matt's Skills V2 (Transactional)`"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def _run_agent_task(self, persona: str, topic: str, use_search: bool = True):
        """運行單個 Agent 任務的包裝器"""
        async with self.semaphore:
            return await asyncio.to_thread(self.gemini.ask_expert_sync, persona, topic, use_search=use_search)

    async def handle_research(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await self.firestore.save_user_chat(chat_id)
        if not context.args:
            await update.message.reply_text("請提供研究主題。範例：`/research 低空經濟發展`")
            return

        topic = " ".join(context.args)
        status_msg = await update.message.reply_text(f"🔍 **啟動專案研究：{topic}**\n\n[⏳] 正在召集專家團隊...")

        try:
            # 1. 第一階段：專家並行分析
            await self._safe_send_or_edit(status_msg, f"🔍 **專案：{topic}**\n\n[⚙️] 專家正在進行獨立分析...")
            
            tasks = [
                self._run_agent_task(PROMPT_DATA_COLLECTOR, f"研究主題：{topic}"),
                self._run_agent_task(PROMPT_CONTEXT_ANALYST, f"研究主題：{topic}"),
                self._run_agent_task(PROMPT_IMPACT_ASSESSOR, f"研究主題：{topic}")
            ]
            
            # return_exceptions=True 確保即使其中一個失敗也不會中斷全部
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 2. 彙整結果與處理異常
            agent_outputs = []
            expert_names = ["數據搜集", "脈絡分析", "趨勢評估"]
            for i, res in enumerate(results):
                if isinstance(res, Exception):
                    logger.error(f"{expert_names[i]} 失敗: {res}")
                    agent_outputs.append(f"[{expert_names[i]}] 錯誤: 無法取得資訊")
                elif not res.get("success"):
                    logger.error(f"{expert_names[i]} 報錯: {res.get('text')}")
                    agent_outputs.append(f"[{expert_names[i]}] 報錯: {res.get('text')}")
                else:
                    agent_outputs.append(f"### {expert_names[i]}分析\n{res['text']}")

            # 3. 第二階段：總編輯彙整
            await self._safe_send_or_edit(status_msg, f"🔍 **專案：{topic}**\n\n[✅] 專家分析完成\n[✍️] 首席總編輯正在撰寫報告...")
            
            cio_input = "\n\n".join(agent_outputs)
            final_res = await self._run_agent_task(PROMPT_CHIEF_EDITOR, f"請彙整以下專家意見：\n{cio_input}", use_search=False)
            
            if final_res.get("success"):
                await self._safe_send_or_edit(status_msg, final_res['text'])
            else:
                await self._safe_send_or_edit(status_msg, f"❌ 報告生成失敗：{final_res.get('text')}")

        except Exception as e:
            logger.error(f"研究流程重大報錯: {e}", exc_info=True)
            await update.message.reply_text(f"❌ 發生非預期錯誤：{e}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        chat_id = update.effective_chat.id
        await self.firestore.save_user_chat(chat_id)
        
        user_text = update.message.text
        if user_text.startswith('/'): return

        CHAT_PERSONA = """你是「互動式研究助理」。請具備搜尋能力回答問題。請盡量提供詳細且專業的回答。
重要：你現在具備「主動紀錄待辦事項」的能力。如果使用者提到未來要做的任務、提醒或計畫，請在回答中自然地提到「我已經幫您記進待辦清單了」。
（注意：實際上後台會自動提取並儲存，你只需要在語氣上確認即可）。"""
        
        # 發送等待狀態
        wait_msg = await update.message.reply_text("🤔 正在思考...")
        
        try:
            # 1. 正常回覆
            res = await self._run_agent_task(CHAT_PERSONA, user_text, use_search=True)
            if res.get("success"):
                await self._safe_send_or_edit(wait_msg, res['text'])
            else:
                await self._safe_send_or_edit(wait_msg, f"⚠️ 報錯：{res.get('text')}")
            
            # 2. 背景任務：分析並提取待辦事項
            asyncio.create_task(self._extract_and_save_todo(chat_id, user_text))
            
        except Exception as e:
            await self._safe_send_or_edit(wait_msg, f"❌ 查詢失敗：{e}")

    async def handle_hide_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """強制移除回覆按鈕選單"""
        from telegram import ReplyKeyboardRemove
        await update.message.reply_text("已嘗試關閉按鈕選單。", reply_markup=ReplyKeyboardRemove())

    async def _extract_and_save_todo(self, chat_id, text):
        """背景提取任務並儲存"""
        try:
            res = await self._run_agent_task(PROMPT_TASK_EXTRACTOR, f"對話內容：{text}", use_search=False)
            if res.get("success") and res['text'].strip() != "NONE":
                tasks = res['text'].strip().split('\n')
                for task in tasks:
                    if task.strip():
                        await self.firestore.add_todo(chat_id, task.strip())
        except Exception as e:
            logger.error(f"提取待辦事項失敗: {e}")

    async def handle_list_todos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await self.firestore.save_user_chat(chat_id)
        
        todos = await self.firestore.get_pending_todos(chat_id)
        if not todos:
            await update.message.reply_text("🎉 目前沒有未完成的待辦事項！")
            return

        text = "📝 **您的未完成事項清單：**\n\n"
        for i, todo in enumerate(todos, 1):
            text += f"{i}. {todo['task']}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
