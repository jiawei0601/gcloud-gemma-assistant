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
