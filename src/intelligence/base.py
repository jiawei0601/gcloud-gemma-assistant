from abc import ABC, abstractmethod
from typing import List
from src.shared.models import ResearchTask, InformationFragment, ResearchArtifact

class BaseIntelligenceProvider(ABC):
    """
    智慧供應商抽象基類。
    所有具體的 AI 實作（例如 OpenAIProvider, ClaudeProvider）都必須繼承此類別並實作核心方法。
    """

    @abstractmethod
    async def process_task(self, task: ResearchTask) -> ResearchTask:
        """
        核心處理方法：接收一個研究任務，根據當前狀態進行推理、分析或規劃，並回傳更新後的任務。
        """
        pass

    @abstractmethod
    async def analyze_fragment(self, fragment: InformationFragment) -> str:
        """
        分析單一資訊碎片。
        """
        pass

    @abstractmethod
    async def generate_plan(self, goal: str) -> List[str]:
        """
        根據研究目標生成研究步驟規劃。
        """
        pass

    @abstractmethod
    async def summarize_artifacts(self, task: ResearchTask) -> ResearchArtifact:
        """
        根據目前任務中所有的碎片，生成一個結構化的研究成果。
        """
        pass
