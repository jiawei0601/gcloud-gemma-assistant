import asyncio
import logging
import os
import http.server
import threading
from dotenv import load_dotenv

from src.core.orchestrator import Orchestrator
from src.intelligence.factory import IntelligenceFactory
from src.communication.telegram_adapter import TelegramAdapter

# 加載環境變數
load_dotenv()

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        # 抑制標準日誌以保持乾淨
        return

def run_health_check_server():
    """啟動一個極簡的 HTTP Server 以通過 Cloud Run 的健康檢查"""
    port = int(os.getenv("PORT", "8080"))
    server_address = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(server_address, HealthCheckHandler)
    logging.info(f"✅ 健康檢查伺服器已啟動於 0.0.0.0:{port}")
    httpd.serve_forever()

async def main():
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 1. 啟動健康檢查伺服器（背景執行）
    threading.Thread(target=run_health_check_server, daemon=True).start()

    # 2. 初始化核心組件 (透過工廠建立 Provider)
    intelligence_svc = IntelligenceFactory.create_provider()
    orchestrator = Orchestrator(intelligence_provider=intelligence_svc)
    
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
