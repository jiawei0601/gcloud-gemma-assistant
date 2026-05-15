import asyncio
import logging
from src.core.orchestrator import Orchestrator
from src.intelligence.gemma import GemmaIntelligenceProvider, GemmaConfig

async def main():
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化組件
    # 這裡我們使用自訂的 Gemma 4 Provider
    gemma_svc = GemmaIntelligenceProvider()
    
    # 初始化編排器
    orchestrator = Orchestrator(intelligence_provider=gemma_svc)
    
    # 執行測試研究
    try:
        goal = "2026年全球半導體產業發展趨勢"
        result_task = await orchestrator.run_research(
            goal=goal,
            destination_folder="GoogleDrive:/ResearchReports/2026"
        )
        
        print("\n" + "="*50)
        print(f"🏁 研究任務已完成！")
        print(f"目標：{result_task.goal}")
        print(f"狀態：{result_task.status}")
        print(f"產出標題：{result_task.artifacts[0].title if result_task.artifacts else '無'}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ 執行過程中出錯：{e}")

if __name__ == "__main__":
    asyncio.run(main())
