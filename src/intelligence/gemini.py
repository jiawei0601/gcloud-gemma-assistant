import logging
import asyncio
from typing import List, Optional

from src.intelligence.base import BaseIntelligenceProvider
from src.core.exceptions import IntelligenceProviderError, ModelInferenceError
from src.shared.models import ResearchTask, InformationFragment, ResearchArtifact
from src.clients.gemini_client import gemini_client

logger = logging.getLogger(__name__)

class GeminiIntelligenceProvider(BaseIntelligenceProvider):
    """
    Gemini 智慧供應商實作，底層統一調用專案的 gemini_client 封裝。
    """
    def __init__(self):
        logger.info("已初始化 GeminiIntelligenceProvider，底層使用統一 GeminiClient SDK 套件。")

    async def _execute_inference(self, system_instruction: str, user_prompt: str) -> str:
        """
        以非同步執行緒方式安全調用同步的 gemini_client 進行推理。
        """
        try:
            logger.info("🚀 透過統一 GeminiClient 發送推理請求...")
            res = await asyncio.to_thread(
                gemini_client.ask_expert_sync,
                persona=system_instruction,
                prompt=user_prompt,
                use_search=False
            )
            
            if not res.get("success"):
                raise ModelInferenceError(f"Gemini 呼叫失敗: {res.get('text')}")
            
            return res["text"]
        except Exception as e:
            logger.error(f"⚠️ Gemini 推理執行失敗: {e}")
            raise ModelInferenceError(f"推理執行失敗: {str(e)}") from e

    async def generate_plan(self, goal: str) -> List[str]:
        """
        根據研究目標生成研究步驟規劃。
        """
        system_instruction = "你是一個專業的策略規劃 AI。請將研究任務拆解為簡短的執行步驟，以逗號分隔。"
        user_prompt = f"研究目標：{goal}\n請提供 3 個關鍵執行步驟。"
        response_text = await self._execute_inference(system_instruction, user_prompt)
        
        # 簡單解析逗號分隔的步驟，回退為預設步驟
        try:
            steps = [s.strip() for s in response_text.split(',') if s.strip()]
            if len(steps) >= 2:
                return steps
        except:
            pass
        return ["搜尋相關產業報告", "分析市場競爭力", "總結發展趨勢"]

    async def analyze_fragment(self, fragment: InformationFragment) -> str:
        """
        分析單一資訊碎片。
        """
        system_instruction = "你是一個資深資訊分析師，請摘要以下內容的關鍵資訊。"
        user_prompt = f"內容：{fragment.content}"
        return await self._execute_inference(system_instruction, user_prompt)

    async def summarize_artifacts(self, task: ResearchTask) -> ResearchArtifact:
        """
        根據目前任務中所有的碎片，生成一個結構化的研究成果。
        """
        if not task.fragments:
            raise IntelligenceProviderError("沒有足夠的資訊碎片可以進行彙整。")
            
        system_instruction = "你是一個資深研究員，請將以下所有資訊碎片彙整成一份結構化的研究報告。請使用 Markdown 格式。"
        fragments_text = "\n".join([f"來源: {f.source}\n內容: {f.content}" for f in task.fragments])
        user_prompt = f"研究目標：{task.goal}\n資訊碎片：\n{fragments_text}"
        
        summary_content = await self._execute_inference(system_instruction, user_prompt)
        
        return ResearchArtifact(
            title=f"研究報告：{task.goal} (由 Gemini 彙整)",
            artifact_type="research_report",
            content=summary_content,
            related_fragment_ids=[f.id for f in task.fragments]
        )

    async def process_task(self, task: ResearchTask) -> ResearchTask:
        logger.info(f"Gemini 正在處理任務：{task.id}")
        task.update_timestamp()
        return task
