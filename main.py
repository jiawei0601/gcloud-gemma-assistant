import asyncio
import logging
import os
from dotenv import load_dotenv

from src.core.orchestrator import Orchestrator
from src.intelligence.gemma import GemmaIntelligenceProvider
from src.communication.telegram_adapter import TelegramAdapter

# 加載環境變數
load_dotenv()

async def main():
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 1. 初始化核心組件
    gemma_svc = GemmaIntelligenceProvider()
    orchestrator = Orchestrator(intelligence_provider=gemma_svc)
    
    # 2. 檢查 Telegram Token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if bot_token:
        # 啟動 Telegram Bot 模式
        logger = logging.getLogger("Main")
        logger.info("檢測到 TELEGRAM_BOT_TOKEN，正在啟動 Telegram 助理模式...")
        
        tg_adapter = TelegramAdapter(bot_token, orchestrator)
        await tg_adapter.run()
    else:
        # 降級為 CLI 測試模式
        print("\n未檢測到 TELEGRAM_BOT_TOKEN，執行單次 CLI 測試研究...")
        try:
            goal = "2026年全球半導體產業發展趨勢"
            result_task = await orchestrator.run_research(
                goal=goal,
                destination_folder="GoogleDrive:/ResearchReports/2026"
            )
            print(f"\n🏁 研究任務已完成！結果：{result_task.status}")
        except Exception as e:
            print(f"❌ 執行過程中出錯：{e}")

if __name__ == "__main__":
    asyncio.run(main())
