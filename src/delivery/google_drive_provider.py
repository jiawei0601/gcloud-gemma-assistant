import io
import logging
from typing import Optional
from googleapiclient.http import MediaIoBaseUpload
from src.delivery.base import BaseDeliveryProvider
from src.delivery.engine import GoogleDeliveryEngine

logger = logging.getLogger(__name__)

class GoogleDriveProvider(BaseDeliveryProvider):
    """Google Drive 交付供應商實作"""
    
    def __init__(self, engine: GoogleDeliveryEngine):
        self.engine = engine

    async def create_folder(self, folder_name: str) -> str:
        service = await self.engine.get_service('drive', 'v3')
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        request = service.files().create(body=file_metadata, fields='id')
        response = await self.engine.execute_api(request)
        return response.get('id')

    async def upload_file(self, content: str, filename: str, parent_id: Optional[str] = None) -> str:
        service = await self.engine.get_service('drive', 'v3')
        file_metadata = {'name': filename}
        if parent_id:
            file_metadata['parents'] = [parent_id]

        fh = io.BytesIO(content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)
        
        request = service.files().create(body=file_metadata, media_body=media, fields='id')
        response = await self.engine.execute_api(request)
        return response.get('id')

    async def get_shareable_link(self, file_id: str) -> str:
        service = await self.engine.get_service('drive', 'v3')
        
        # 設定權限為任何人可讀
        perm_request = service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        )
        await self.engine.execute_api(perm_request)
        
        # 獲取連結
        get_request = service.files().get(fileId=file_id, fields='webViewLink')
        response = await self.engine.execute_api(get_request)
        return response.get('webViewLink')

    async def create_document_from_text(self, title: str, content: str, parent_id: Optional[str] = None) -> str:
        """透過上傳 HTML 並由 Drive API 自動轉換為 Google Docs 格式"""
        service = await self.engine.get_service('drive', 'v3')
        
        # 簡單的 HTML 封裝以利格式轉換
        safe_content = content.replace('\n', '<br>')
        html_content = f"<html><body><h2>{title}</h2><p>{safe_content}</p></body></html>"
        
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.document'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        fh = io.BytesIO(html_content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/html', resumable=True)
        
        request = service.files().create(body=file_metadata, media_body=media, fields='id')
        response = await self.engine.execute_api(request)
        return response.get('id')
