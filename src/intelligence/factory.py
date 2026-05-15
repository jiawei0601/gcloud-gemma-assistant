import os
import logging
from typing import Optional

from src.intelligence.base import BaseIntelligenceProvider
from src.intelligence.gemma import GemmaIntelligenceProvider
from src.intelligence.gemini import GeminiIntelligenceProvider

logger = logging.getLogger(__name__)

class IntelligenceFactory:
    """
    供應商工廠，負責根據環境配置建立正確的智慧供應商實例。
    """
    
    @staticmethod
    def create_provider() -> BaseIntelligenceProvider:
        # 根據環境變數決定使用哪個供應商，預設使用 gemma (本地)
        provider_type = os.getenv("INTELLIGENCE_PROVIDER", "gemma").lower()
        
        if provider_type == "gemini":
            logger.info("根據配置建立 Gemini 供應商 (Cloud 模式)")
            return GeminiIntelligenceProvider()
        elif provider_type == "gemma":
            logger.info("根據配置建立 Gemma 供應商 (Local 模式)")
            return GemmaIntelligenceProvider()
        else:
            logger.warning(f"未知的供應商類型 '{provider_type}'，降級使用 Gemma。")
            return GemmaIntelligenceProvider()
