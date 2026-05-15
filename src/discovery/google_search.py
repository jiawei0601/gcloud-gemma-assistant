import os
import httpx
import logging
from typing import List, Dict
from src.discovery.base import BaseDiscoveryProvider

logger = logging.getLogger(__name__)

class GoogleSearchProvider(BaseDiscoveryProvider):
    """使用 Google Custom Search API 的搜尋供應商"""
    
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cx = search_engine_id or os.getenv("GOOGLE_SEARCH_CX")
        self.endpoint = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        if not self.api_key or not self.cx:
            logger.warning("Google Search API Key 或 CX 未設定，將回傳空結果。")
            return []

        params = {
            "q": query,
            "key": self.api_key,
            "cx": self.cx,
            "num": num_results
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.endpoint, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet")
                    })
                return results
            except Exception as e:
                logger.error(f"Google 搜尋執行失敗：{str(e)}")
                return []
