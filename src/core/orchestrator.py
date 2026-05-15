import asyncio
import logging
from typing import List, Optional

from src.shared.models import ResearchTask, TaskStatus, InformationFragment, ResearchArtifact
from src.intelligence.base import BaseIntelligenceProvider
from src.discovery.engine import DiscoveryEngine
from src.delivery.base import BaseDeliveryProvider
from src.core.exceptions import AssistantError

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    研究流程的指揮中心。
    負責串聯 Discovery -> Intelligence -> Delivery 的非同步工作流。
    """

    def __init__(
        self,
        intelligence_provider: BaseIntelligenceProvider,
        discovery_engine: Optional[DiscoveryEngine] = None,
        delivery_provider: Optional[BaseDeliveryProvider] = None
    ):
        self.intelligence = intelligence_provider
        self.discovery = discovery_engine or DiscoveryEngine()
        self.delivery = delivery_provider

    async def run_research(self, goal: str, destination_folder: str) -> ResearchTask:
        """
        執行完整的研發流程。
        """
        logger.info(f"🚀 開始執行研究任務：'{goal}'")
        
        # 初始化任務
        task = ResearchTask(goal=goal, status=TaskStatus.IN_PROGRESS)
        
        try:
            # 1. 規劃階段
            plan = await self.intelligence.generate_plan(goal)
            task.description = f"執行計畫：{', '.join(plan)}"
            logger.info("✅ 規劃階段完成。")

            # 2. 探索階段 (真實網路探索)
            fragments = await self.discovery.fetch_information(goal)
            task.fragments.extend(fragments)
            logger.info(f"✅ 探索階段完成，取得 {len(fragments)} 個碎片。")

            # 3. 綜合階段 (Intelligence)
            artifact = await self.intelligence.summarize_artifacts(task)
            task.artifacts.append(artifact)
            logger.info("✅ 綜合彙整完成。")

            # 4. 交付階段 (寫入 Google Drive)
            if self.delivery:
                doc_id = await self.delivery.create_document_from_text(
                    title=artifact.title,
                    content=artifact.content
                )
                link = await self.delivery.get_shareable_link(doc_id)
                logger.info(f"✅ 交付階段完成。報告已存放在 Google Drive: {link}")
                # 更新成果的 Metadata 以便後續存取
                artifact.metadata["google_drive_link"] = link
            else:
                logger.info(f"⚠️ 未配置 Delivery Provider，僅完成模擬交付至：{destination_folder}")

            task.status = TaskStatus.COMPLETED
            task.update_timestamp()
            return task

        except Exception as e:
            task.status = TaskStatus.FAILED
            logger.error(f"❌ 研究流程失敗：{str(e)}")
            raise AssistantError(f"任務執行失敗：{str(e)}") from e
