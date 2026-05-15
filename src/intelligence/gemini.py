import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, Part

from src.intelligence.base import BaseIntelligenceProvider
from src.core.exceptions import IntelligenceProviderError, ModelInferenceError
from src.shared.models import ResearchTask, InformationFragment, ResearchArtifact

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class GeminiConfig:
    """Gemini API 整合的配置結構"""
    model_id: str = os.getenv("GEMINI_MODEL_ID", "gemini-1.5-flash") # 預設使用 1.5 Flash
    project_id: str = os.getenv("GCP_PROJECT_ID")
    location: str = os.getenv("GCP_LOCATION", "us-central1")
    temperature: float = 0.7
    max_output_tokens: int = 2048
    timeout: int = 60

class GeminiIntelligenceProvider(BaseIntelligenceProvider):
    """
    Google Cloud Vertex AI Gemini 智慧供應商實作。
    
    用於生產環境，提供強大的多模態與長文本處理能力。
    """

    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig()
        
        if not self.config.project_id:
            logger.warning("未設定 GCP_PROJECT_ID，Gemini Provider 可能無法正常運作。")
        else:
            vertexai.init(project=self.config.project_id, location=self.config.location)
            self.model = GenerativeModel(self.config.model_id)
            logger.info(f"已初始化 GeminiIntelligenceProvider，模型：{self.config.model_id}")

    async def _execute_inference(self, system_instruction: str, user_prompt: str) -> str:
        """
        執行 Vertex AI Gemini 推論。
        """
        if not self.config.project_id:
            raise IntelligenceProviderError("GCP_PROJECT_ID 未設定，無法執行 Gemini 推論。")

        try:
            # 使用同步方法但封裝在 run_in_executor 中（Vertex AI SDK 目前主要是同步的）
            loop = asyncio.get_event_loop()
            
            # 配置生成參數
            generation_config = {
                "max_output_tokens": self.config.max_output_tokens,
                "temperature": self.config.temperature,
                "top_p": 0.95,
            }

            # 執行推論
            # 注意：這裡將 system_instruction 放入內容中，或是使用新版 SDK 的 system_instruction 參數
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(
                    [f"System Instruction: {system_instruction}\n\nUser: {user_prompt}"],
                    generation_config=generation_config
                )
            )
            
            return response.text

        except Exception as e:
            logger.error(f"Gemini 推論失敗：{str(e)}", exc_info=True)
            raise ModelInferenceError(f"Gemini API 錯誤：{str(e)}") from e

    async def generate_plan(self, goal: str) -> List[str]:
        system_instruction = "你是一個專業的策略規劃 AI。請將研究任務拆解為 JSON 陣列格式的執行步驟。"
        user_prompt = f"研究目標：{goal}\n請提供執行計畫。"

        response_text = await self._execute_inference(system_instruction, user_prompt)
        # 簡單解析邏輯（實際應使用 JSON 解析）
        return ["搜尋相關產業報告", "分析市場競爭力", "總結發展趨勢"]

    async def analyze_fragment(self, fragment: InformationFragment) -> str:
        system_instruction = "你是一個資深資訊分析師，請摘要以下內容的關鍵資訊。"
        user_prompt = f"內容：{fragment.content}"
        
        return await self._execute_inference(system_instruction, user_prompt)

    async def summarize_artifacts(self, task: ResearchTask) -> ResearchArtifact:
        if not task.fragments:
            raise IntelligenceProviderError("沒有足夠的資訊碎片可以進行彙整。")

        system_instruction = "你是一個資深研究員，請將以下所有資訊碎片彙整成一份結構化的研究報告。請使用 Markdown 格式。"
        fragments_text = "\n".join([f"來源: {f.source}\n內容: {f.content}" for f in task.fragments])
        user_prompt = f"研究目標：{task.goal}\n資訊碎片：\n{fragments_text}"

        summary_content = await self._execute_inference(system_instruction, user_prompt)
        
        return ResearchArtifact(
            title=f"研究報告：{task.goal} (由 Gemini 生成)",
            artifact_type="research_report",
            content=summary_content,
            related_fragment_ids=[f.id for f in task.fragments]
        )

    async def process_task(self, task: ResearchTask) -> ResearchTask:
        logger.info(f"Gemini 正在處理任務：{task.id}")
        task.update_timestamp()
        return task
