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

    async def read_document(self, document_id: str) -> str:
        """讀取 Google Doc 內容並回傳純文字"""
        service = await self.engine.get_service('docs', 'v1')
        request = service.documents().get(documentId=document_id)
        doc = await self.engine.execute_api(request)
        
        text = ""
        doc_content = doc.get('body', {}).get('content', [])
        for element in doc_content:
            if 'paragraph' in element:
                elements = element.get('paragraph', {}).get('elements', [])
                for text_run in elements:
                    if 'textRun' in text_run:
                        text += text_run.get('textRun', {}).get('content', '')
        return text

    async def append_to_document(self, document_id: str, text: str) -> None:
        """在 Google Doc 尾端追加文字"""
        service = await self.engine.get_service('docs', 'v1')
        body = {
            'requests': [
                {
                    'insertText': {
                        'text': text,
                        'endOfSegmentLocation': {
                            'segmentId': ''
                        }
                    }
                }
            ]
        }
        request = service.documents().batchUpdate(documentId=document_id, body=body)
        await self.engine.execute_api(request)

    async def create_spreadsheet(self, title: str, parent_id: Optional[str] = None) -> str:
        """建立 Google Sheet 並回傳 spreadsheet_id"""
        service = await self.engine.get_service('sheets', 'v4')
        spreadsheet_body = {
            'properties': {
                'title': title
            }
        }
        request = service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId')
        response = await self.engine.execute_api(request)
        spreadsheet_id = response.get('spreadsheetId')
        
        if parent_id and spreadsheet_id:
            drive_service = await self.engine.get_service('drive', 'v3')
            file_req = drive_service.files().get(fileId=spreadsheet_id, fields='parents')
            file_res = await self.engine.execute_api(file_req)
            previous_parents = ",".join(file_res.get('parents', []))
            
            move_req = drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=parent_id,
                removeParents=previous_parents,
                fields='id, parents'
            )
            await self.engine.execute_api(move_req)
            
        return spreadsheet_id

    async def read_spreadsheet(self, spreadsheet_id: str, range_name: str) -> list:
        """讀取 Google Sheet 指定範圍的數據"""
        service = await self.engine.get_service('sheets', 'v4')
        request = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        )
        response = await self.engine.execute_api(request)
        return response.get('values', [])

    async def update_spreadsheet_values(self, spreadsheet_id: str, range_name: str, values: list) -> None:
        """更新 Google Sheet 指定範圍的單元格數據"""
        service = await self.engine.get_service('sheets', 'v4')
        body = {
            'values': values
        }
        request = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        )
        await self.engine.execute_api(request)
