import os
import io
import logging
import asyncio
from typing import Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleDeliveryEngine:
    """
    深層模組 (Deep Module)：封裝所有 Google API 的複雜度。
    負責 OAuth2 驗證、Token 管理、重試邏輯與底層 API 呼叫。
    """
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._drive_service = None
        self._docs_service = None
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/spreadsheets'
        ]

    async def _get_credentials(self):
        """獲取或刷新 OAuth2 憑證"""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                await asyncio.get_event_loop().run_in_executor(None, creds.refresh, Request())
            elif os.path.exists(self.credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.scopes)
                creds = await asyncio.get_event_loop().run_in_executor(None, flow.run_local_server, 0)
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            else:
                logger.info("🔑 [GoogleDeliveryEngine] 未偵測到 credentials.json，正在嘗試使用 Application Default Credentials (ADC)...")
                try:
                    import google.auth
                    creds, project = google.auth.default(scopes=self.scopes)
                    logger.info("✅ [GoogleDeliveryEngine] 成功取得 Application Default Credentials (ADC)！")
                except Exception as e:
                    logger.error(f"❌ [GoogleDeliveryEngine] 無法取得 Application Default Credentials: {e}")
                    raise e
        return creds

    async def get_service(self, service_name: str, version: str):
        """通用獲取 Google Service 的方法"""
        creds = await self._get_credentials()
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: build(service_name, version, credentials=creds)
        )

    async def execute_api(self, request):
        """非同步執行 API 請求並處理重試邏輯"""
        loop = asyncio.get_event_loop()
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await loop.run_in_executor(None, request.execute)
            except HttpError as e:
                if e.resp.status in [429, 503] and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Google API 回傳 {e.resp.status}，正在重試 ({attempt+1}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                    continue
                raise e
