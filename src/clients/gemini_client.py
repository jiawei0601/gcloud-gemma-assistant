import logging
import asyncio
import csv
from io import StringIO
from google import genai
from google.genai import types
from typing import Tuple, Dict, Any, Optional
from config import config

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.project_id = config.PROJECT_ID
        self.location = config.LOCATION
        self.model_id = getattr(config, "GEMINI_MODEL_ID", "gemini-2.5-pro")
        self.drive_provider = None
        self.main_loop = None
        
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

    def set_drive_provider(self, drive_provider, main_loop):
        """傳入雲端硬碟供應商實例與背景 Async Event Loop"""
        self.drive_provider = drive_provider
        self.main_loop = main_loop
        logging.info("[GeminiClient] Google Drive / Docs / Sheets 整合工具成功載入！")

    # --- Google Docs & Sheets 整合工具集 (Exposed to LLM via Function Calling) ---

    def create_google_doc(self, title: str, content: str) -> str:
        """建立一個新 Google 文件 (Google Doc)，寫入內容，並回傳建立結果與可分享的 webWebViewLink 連結。
        參數:
          title: 文件的標題
          content: 文件的文字內容
        """
        if not self.drive_provider or not self.main_loop:
            return "錯誤：Google Drive 服務未在背景執行緒中初始化"
        
        async def _run():
            doc_id = await self.drive_provider.create_document_from_text(title, content)
            link = await self.drive_provider.get_shareable_link(doc_id)
            return f"成功建立 Google 文件！\n文件 ID: {doc_id}\n分享連結: {link}"
            
        try:
            future = asyncio.run_coroutine_threadsafe(_run(), self.main_loop)
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"create_google_doc failed: {e}", exc_info=True)
            return f"建立文件失敗: {e}"

    def read_google_doc(self, document_id: str) -> str:
        """讀取已存在的 Google 文件 (Google Doc) 的純文字內容。
        參數:
          document_id: Google 文件的唯一 ID
        """
        if not self.drive_provider or not self.main_loop:
            return "錯誤：Google Drive 服務未在背景執行緒中初始化"
        
        async def _run():
            return await self.drive_provider.read_document(document_id)
            
        try:
            future = asyncio.run_coroutine_threadsafe(_run(), self.main_loop)
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"read_google_doc failed: {e}", exc_info=True)
            return f"讀取文件失敗: {e}"

    def append_google_doc(self, document_id: str, text: str) -> str:
        """在已存在的 Google 文件 (Google Doc) 的最尾端追加新文字內容。
        參數:
          document_id: Google 文件的唯一 ID
          text: 要追加的文字內容
        """
        if not self.drive_provider or not self.main_loop:
            return "錯誤：Google Drive 服務未在背景執行緒中初始化"
        
        async def _run():
            await self.drive_provider.append_to_document(document_id, text)
            return f"成功在文件 {document_id} 尾端追加文字。"
            
        try:
            future = asyncio.run_coroutine_threadsafe(_run(), self.main_loop)
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"append_google_doc failed: {e}", exc_info=True)
            return f"追加文件內容失敗: {e}"

    def create_google_sheet(self, title: str) -> str:
        """建立一個新 Google 試算表 (Google Sheet)，並回傳建立結果與可分享的 webWebViewLink 連結。
        參數:
          title: 試算表的標題
        """
        if not self.drive_provider or not self.main_loop:
            return "錯誤：Google Drive 服務未在背景執行緒中初始化"
        
        async def _run():
            sheet_id = await self.drive_provider.create_spreadsheet(title)
            link = await self.drive_provider.get_shareable_link(sheet_id)
            return f"成功建立 Google 試算表！\n試算表 ID: {sheet_id}\n分享連結: {link}"
            
        try:
            future = asyncio.run_coroutine_threadsafe(_run(), self.main_loop)
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"create_google_sheet failed: {e}", exc_info=True)
            return f"建立試算表失敗: {e}"

    def read_google_sheet(self, spreadsheet_id: str, range_name: str = "Sheet1!A1:Z100") -> str:
        """讀取已存在的 Google 試算表 (Google Sheet) 指定範圍內的所有單元格資料並回傳。
        參數:
          spreadsheet_id: Google 試算表的唯一 ID
          range_name: 範圍名稱，預設為 'Sheet1!A1:Z100'
        """
        if not self.drive_provider or not self.main_loop:
            return "錯誤：Google Drive 服務未在背景執行緒中初始化"
        
        async def _run():
            values = await self.drive_provider.read_spreadsheet(spreadsheet_id, range_name)
            if not values:
                return "此範圍內無任何資料。"
            lines = []
            for row in values:
                lines.append(" | ".join(str(cell) for cell in row))
            return "\n".join(lines)
            
        try:
            future = asyncio.run_coroutine_threadsafe(_run(), self.main_loop)
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"read_google_sheet failed: {e}", exc_info=True)
            return f"讀取試算表失敗: {e}"

    def update_google_sheet(self, spreadsheet_id: str, range_name: str, csv_data: str) -> str:
        """更新或修改已存在的 Google 試算表 (Google Sheet) 的單元格數值。
        參數:
          spreadsheet_id: Google 試算表的唯一 ID
          range_name: 更新範圍 (例如 'Sheet1!A1:D5')
          csv_data: 寫入的二維數據，請使用逗號與換行符分隔的 CSV 格式字串
        """
        if not self.drive_provider or not self.main_loop:
            return "錯誤：Google Drive 服務未在背景執行緒中初始化"
        
        f = StringIO(csv_data)
        reader = csv.reader(f)
        values = list(reader)
        
        async def _run():
            await self.drive_provider.update_spreadsheet_values(spreadsheet_id, range_name, values)
            return f"成功更新試算表 {spreadsheet_id} 範圍 {range_name} 內的資料。"
            
        try:
            future = asyncio.run_coroutine_threadsafe(_run(), self.main_loop)
            return future.result(timeout=30)
        except Exception as e:
            logger.error(f"update_google_sheet failed: {e}", exc_info=True)
            return f"更新試算表失敗: {e}"

    # --- 核心詢問入口 ---

    def ask_expert_sync(self, persona: str, prompt: str, use_search: bool = True, use_drive: bool = False) -> Dict[str, Any]:
        """
        同步調用專家 Agent。
        """
        if not self.client:
            return {"text": "Client 未初始化", "success": False}

        # 組合工具集
        api_tools = []
        if use_search:
            api_tools.append(types.Tool(google_search=types.GoogleSearch()))
        
        # 只有在明確啟用且加載了雲端硬碟服務時，才載入 Docs & Sheets 工具 (不與 Google Search 混用)
        if use_drive and self.drive_provider:
            api_tools.extend([
                self.create_google_doc,
                self.read_google_doc,
                self.append_google_doc,
                self.create_google_sheet,
                self.read_google_sheet,
                self.update_google_sheet
            ])
        
        safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_CIVIC_INTEGRITY", threshold="BLOCK_ONLY_HIGH"),
        ]

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=persona,
                    tools=api_tools,
                    temperature=0.2,
                    safety_settings=safety_settings
                )
            )
            
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
