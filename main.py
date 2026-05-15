import asyncio
import logging
import os
import http.server
import threading
import sys
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

# 配置基礎日誌，確保一啟動就有輸出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("Main")

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return

def run_health_check_server():
    """啟動一個極簡的 HTTP Server 以通過 Cloud Run 的健康檢查"""
    port = int(os.getenv("PORT", "8080"))
    try:
        server_address = ('0.0.0.0', port)
        httpd = http.server.HTTPServer(server_address, HealthCheckHandler)
        logger.info(f"✅ 健康檢查伺服器已啟動於 0.0.0.0:{port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"❌ 健康檢查伺服器啟動失敗: {e}")

# 立即在背景啟動健康檢查，確保 Cloud Run 能儘快偵測到埠號
health_thread = threading.Thread(target=run_health_check_server, daemon=True)
health_thread.start()

# 延遲導入其他模組，避免啟動初期因大型庫加載過慢導致超時
from src.core.orchestrator import Orchestrator
from src.intelligence.factory import IntelligenceFactory
from src.communication.telegram_adapter import TelegramAdapter

async def main():
    logger.info("🚀 應用程式正在初始化...")
    
    try:
        # 1. 初始化核心組件
        intelligence_svc = IntelligenceFactory.create_provider()
        orchestrator = Orchestrator(intelligence_provider=intelligence_svc)
        
        # 2. 檢查 Telegram Token
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if bot_token:
            logger.info("檢測到 TELEGRAM_BOT_TOKEN，正在啟動 Telegram 助理模式...")
            tg_adapter = TelegramAdapter(bot_token, orchestrator)
            
            # 啟動時發送通知給管理員 (若有設定)
            admin_id = os.getenv("ADMIN_CHAT_ID")
            if admin_id:
                # 建立一個非同步任務來發送通知，以免阻塞啟動流程
                asyncio.create_task(tg_adapter.send_startup_notification(admin_id))
                
            await tg_adapter.run()
        else:
            logger.warning("未檢測到 TELEGRAM_BOT_TOKEN，進入 CLI 閒置模式。")
            # 在 Cloud Run 上如果沒有 Token，保持運行以避免重啟循環
            while True:
                await asyncio.sleep(3600)
                
    except Exception as e:
        logger.critical(f"💥 啟動過程中發生嚴重錯誤: {e}", exc_info=True)
        # 發生錯誤時不要立即退出，讓日誌有機會上傳，並讓健康檢查繼續運行一段時間以便排錯
        await asyncio.sleep(60)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 正在關閉程式...")
