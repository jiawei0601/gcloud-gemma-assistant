import logging
from typing import List, Optional
from src.discovery.google_search import GoogleSearchProvider
from src.discovery.scraper import WebScraper
from src.shared.models import InformationFragment

logger = logging.getLogger(__name__)

class DiscoveryEngine:
    """
    深層模組 (Deep Module)：封裝搜尋與抓取的複雜細節。
    對外僅提供簡潔的資訊獲取介面。
    """
    
    def __init__(
        self, 
        search_provider: Optional[GoogleSearchProvider] = None,
        scraper: Optional[WebScraper] = None
    ):
        self.search_provider = search_provider or GoogleSearchProvider()
        self.scraper = scraper or WebScraper()

    async def fetch_information(self, query: str, max_links: int = 3) -> List[InformationFragment]:
        """
        核心介面：根據查詢語句獲取相關的資訊碎片。
        """
        logger.info(f"正在針對『{query}』執行網路探索...")
        
        # 1. 執行搜尋
        search_results = await self.search_provider.search(query, num_results=max_links + 2)
        if not search_results:
            logger.info("未找到相關搜尋結果。")
            return []

        fragments = []
        
        # 2. 針對前幾個結果進行深度抓取
        for i, res in enumerate(search_results[:max_links]):
            link = res["link"]
            title = res["title"]
            
            # 先加入搜尋摘要作為基本碎片
            fragments.append(InformationFragment(
                content=res["snippet"],
                source=link,
                metadata={"title": title, "type": "search_snippet"}
            ))
            
            # 嘗試抓取全文
            full_content = await self.scraper.scrape(link)
            if full_content:
                fragments.append(InformationFragment(
                    content=full_content,
                    source=link,
                    metadata={"title": title, "type": "full_page_content"}
                ))
            
            if len(fragments) >= max_links * 2:
                break
                
        logger.info(f"網路探索完成，獲得 {len(fragments)} 個資訊碎片。")
        return fragments
