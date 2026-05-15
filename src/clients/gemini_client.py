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
        self.model_id = "gemini-1.5-flash" # 切換為穩定版本以解決 404 錯誤
        
        try:
            self.client = genai.Client(
                vertexai=True, 
                project=self.project_id, 
                location=self.location
            )
            logging.info(f"[GeminiClient] 專業版初始化成功 (Project: {self.project_id})")
        except Exception as e:
            logging.error(f"[GeminiClient] 初始化失敗: {e}")
            self.client = None

    async def ask_expert(self, persona: str, prompt: str, use_search: bool = True) -> Dict[str, Any]:
        """
        異步調用特定人設的專家 Agent。
        """
        if not self.client:
            return {"text": "Client 未初始化", "success": False}

        tools = [types.Tool(google_search=types.GoogleSearch())] if use_search else []
        
        try:
            # 使用 aio 異步接口進行非阻塞調用
            response = await self.client.aio.models.generate_content(
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
            logging.error(f"[GeminiClient] 專家調用失敗: {e}")
            return {"success": False, "text": str(e)}

    def ask(self, prompt: str) -> Tuple[bool, str]:
        """
        傳統同步接口 (保留相容性，內部執行簡單生成)
        """
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
