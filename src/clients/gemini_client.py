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
        
        safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_CIVIC_INTEGRITY", threshold="BLOCK_ONLY_HIGH"),
        ]

        try:
            # 改回同步調用，避免迴圈衝突
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=persona,
                    tools=tools,
                    temperature=0.2,
                    safety_settings=safety_settings
                )
            )
            
            # 檢查是否有候選回應
            if not response.candidates or not response.candidates[0].content.parts:
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                error_msg = f"模型未生成內容 (原因: {finish_reason})"
                logging.warning(f"[GeminiClient] {error_msg}")
                return {"success": False, "text": error_msg}

            return {
                "success": True,
                "text": response.text,
                "usage": response.usage_metadata
            }
        except Exception as e:
            logging.error(f"[GeminiClient] 專家同步調用失敗: {e}")
            return {"success": False, "text": f"API 錯誤: {str(e)}"}

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
