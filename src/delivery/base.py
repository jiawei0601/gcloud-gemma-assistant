from abc import ABC, abstractmethod
from typing import Optional

class BaseDeliveryProvider(ABC):
    """定義交付供應商的標準介面"""

    @abstractmethod
    async def create_folder(self, folder_name: str) -> str:
        """建立資料夾並回傳 folder_id"""
        pass

    @abstractmethod
    async def upload_file(self, content: str, filename: str, parent_id: Optional[str] = None) -> str:
        """上傳檔案並回傳 file_id"""
        pass

    @abstractmethod
    async def get_shareable_link(self, file_id: str) -> str:
        """獲取檔案的可分享連結"""
        pass

    @abstractmethod
    async def create_document_from_text(self, title: str, content: str, parent_id: Optional[str] = None) -> str:
        """將文字/Markdown 轉換為文件格式並儲存"""
        pass

    @abstractmethod
    async def read_document(self, document_id: str) -> str:
        """讀取 Google Doc 內容並回傳純文字"""
        pass

    @abstractmethod
    async def append_to_document(self, document_id: str, text: str) -> None:
        """在 Google Doc 尾端追加文字"""
        pass

    @abstractmethod
    async def create_spreadsheet(self, title: str, parent_id: Optional[str] = None) -> str:
        """建立 Google Sheet 並回傳 spreadsheet_id"""
        pass

    @abstractmethod
    async def read_spreadsheet(self, spreadsheet_id: str, range_name: str) -> list:
        """讀取 Google Sheet 指定範圍的數據"""
        pass

    @abstractmethod
    async def update_spreadsheet_values(self, spreadsheet_id: str, range_name: str, values: list) -> None:
        """更新 Google Sheet 指定範圍的單元格數據"""
        pass
