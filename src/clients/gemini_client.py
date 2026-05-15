import logging
import asyncio
from google import genai
from google.genai import types
from typing import Tuple, Dict, Any
from config import config

class GeminiClient:
    def __init__(self):
        self.project_id = config.PROJECT_ID
        self.location = config.LOCATION
        self.model_id = getattr(config, "GEMINI_MODEL_ID", "gemini-1.5-flash-002")
        
        # 使用同步 Client，這對 Cloud Run 的 Webhook 模式最穩定
        try:
            self.client = genai.Client(
                vertexai=True, 
                project=self.project_id, 
                location=self.location
            )
            logging.info(f"[GeminiClient] 同步專業版初始化成功 (Project: {self.project_id})")
        except Exception as e:
            logging.error(f"[GeminiClient] 初始化失敗: {e}")
            self.client = None

    def ask_expert_sync(self, persona: str, prompt: str, use_search: bool = True) -> Dict[str, Any]:
        """
        同步調用專家 Agent。
        """
        if not self.client:
            return {"text": "Client 未初始化", "success": False}

        tools = [types.Tool(google_search=types.GoogleSearch())] if use_search else []
        
        try:
            # 改回同步調用，避免迴圈衝突
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=persona,
                    tools=tools,
                    temperature=0.2,
                )
            )
            
            return {
                "success": True,
                "text": response.text if response.text else "無回應內容",
                "usage": response.usage_metadata
            }
        except Exception as e:
            logging.error(f"[GeminiClient] 專家同步調用失敗: {e}")
            return {"success": False, "text": str(e)}

    def ask(self, prompt: str) -> Tuple[bool, str]:
        if not self.client:
            return False, "Client 未初始化"
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return True, response.text
        except Exception as e:
            return False, str(e)

gemini_client = GeminiClient()
