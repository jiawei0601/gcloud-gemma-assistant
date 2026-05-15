import httpx
import logging
from bs4 import BeautifulSoup
from src.discovery.base import BaseScraper

logger = logging.getLogger(__name__)

class WebScraper(BaseScraper):
    """網頁抓取器，負責 HTML 清洗與純文字擷取"""
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def scrape(self, url: str) -> str:
        logger.debug(f"正在抓取網頁：{url}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 移除噪音標籤
                for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                    element.decompose()

                # 擷取本文文字
                text = soup.get_text(separator=' ')
                
                # 清洗空白字元
                lines = (line.strip() for line in text.splitlines())
                chunks = (chunk for chunk in lines if chunk)
                clean_text = "\n".join(chunks)
                
                # 限制長度以符合 LLM 上下文限制
                return clean_text[:6000] 
        except Exception as e:
            logger.warning(f"抓取 {url} 時發生錯誤：{str(e)}")
            return ""
