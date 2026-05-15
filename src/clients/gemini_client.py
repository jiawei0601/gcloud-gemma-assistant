import logging
from google import genai
from typing import Tuple
from config import config

class GeminiClient:
    def __init__(self):
        self.project_id = config.PROJECT_ID
        self.location = config.LOCATION
        self.model_id = config.GEMINI_MODEL_ID
        
        # 初始化 2026 版 GenAI 客戶端
        # 使用 vertexai=True 確保透過 Vertex AI 調用
        try:
            self.client = genai.Client(
                vertexai=True, 
                project=self.project_id, 
                location=self.location
            )
            logging.info(f"[GeminiClient] 已初始化 (Project: {self.project_id}, Location: {self.location})")
        except Exception as e:
            logging.error(f"[GeminiClient] 初始化失敗: {e}")
            self.client = None

    def ask(self, prompt: str) -> Tuple[bool, str]:
        """
        執行推理任務。回傳 (成功與否, 回應內容或錯誤訊息)。
        """
        if not self.client:
            return False, "Gemini Client 未能正確初始化。"
            
        try:
            logging.info(f"[GeminiClient] 正在調用模型 {self.model_id}...")
            # 使用 SDK 的標準生成方法
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            if response and response.text:
                return True, response.text
            else:
                return False, "模型未回傳任何內容。"
                
        except Exception as e:
            logging.error(f"[GeminiClient] 推理失敗: {e}")
            return False, f"Gemini API 錯誤: {str(e)}"

gemini_client = GeminiClient()
