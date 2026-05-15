from abc import ABC, abstractmethod
from typing import List, Dict

class BaseDiscoveryProvider(ABC):
    """搜尋供應商抽象基類"""
    
    @abstractmethod
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """執行搜尋並回傳結果清單"""
        pass

class BaseScraper(ABC):
    """網頁抓取器抽象基類"""
    
    @abstractmethod
    async def scrape(self, url: str) -> str:
        """抓取網頁內容並回傳清洗後的文字"""
        pass
