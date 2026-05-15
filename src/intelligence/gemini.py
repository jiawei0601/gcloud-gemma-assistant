import os
import logging
import asyncio
import json
import httpx
import google.auth
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from google.auth.transport.requests import Request

from src.intelligence.base import BaseIntelligenceProvider
from src.core.exceptions import IntelligenceProviderError, ModelInferenceError
from src.shared.models import ResearchTask, InformationFragment, ResearchArtifact

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class GeminiConfig:
    """Gemini API 整合的配置結構"""
    model_id: str = os.getenv("GEMINI_MODEL_ID", "gemini-1.5-flash-002")
    project_id: str = os.getenv("GCP_PROJECT_ID")
    location: str = os.getenv("GCP_LOCATION", "asia-east1")
    temperature: float = 0.7
    max_output_tokens: int = 2048
    timeout: int = 60

class GeminiIntelligenceProvider(BaseIntelligenceProvider):
    """
    輕量化 Gemini 供應商：使用 REST API 替代重型 SDK。
    """
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig()
        self.project_id = self.config.project_id
        self.credentials, _ = google.auth.default()
        self.client = httpx.AsyncClient(timeout=float(self.config.timeout))

    async def _get_access_token(self):
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    async def _execute_inference(self, system_instruction: str, user_prompt: str) -> str:
        token = await self._get_access_token()
        url = f"https://{self.config.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.config.location}/publishers/google/models/{self.config.model_id}:generateContent"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Instruction: {system_instruction}\n\nUser: {user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_output_tokens,
                "topP": 0.95,
            }
        }

        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            logger.error(f"Gemini REST API 呼叫失敗: {e}")
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
