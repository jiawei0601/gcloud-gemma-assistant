import asyncio
import logging
import os
import http.server
import threading
import sys
from dotenv import load_dotenv

# 強制刷新 stdout
sys.stdout.reconfigure(line_buffering=True)

# 加載環境變數
load_dotenv()

# 配置基礎日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("Main")

logger.info("🎬 程式入口點啟動...")

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        return

def run_health_check_server():
    port = int(os.getenv("PORT", "8080"))
    try:
        server_address = ('0.0.0.0', port)
        httpd = http.server.HTTPServer(server_address, HealthCheckHandler)
        logger.info(f"✅ 健康檢查伺服器運作中: 0.0.0.0:{port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"❌ 健康檢查伺服器異常: {e}")

# 背景啟動健康檢查
threading.Thread(target=run_health_check_server, daemon=True).start()

async def main():
    logger.info("🚀 進入 main() 非同步主迴圈...")
    
    try:
        # 延遲導入大型庫
        logger.info("📦 正在加載模組與大型程式庫...")
        from src.core.orchestrator import Orchestrator
        from src.intelligence.factory import IntelligenceFactory
        from src.communication.telegram_adapter import TelegramAdapter
        logger.info("✅ 模組加載完成。")

        # 1. 初始化核心組件
        logger.info("⚙️ 正在初始化研究引擎...")
        intelligence_svc = IntelligenceFactory.create_provider()
        orchestrator = Orchestrator(intelligence_provider=intelligence_svc)
        
        # 2. 檢查憑證
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        admin_id = os.getenv("ADMIN_CHAT_ID")
        
        if bot_token:
            logger.info(f"🤖 偵測到 Bot Token (長度: {len(bot_token)})")
            tg_adapter = TelegramAdapter(bot_token, orchestrator)
            
            # 初始化應用程式
            await tg_adapter.initialize()
            
            # 發送啟動通知
            if admin_id:
                logger.info(f"🔔 嘗試發送啟動通知給管理員: {admin_id}")
                await tg_adapter.send_startup_notification(admin_id)
            
            # 啟動輪詢
            logger.info("📡 啟動 Telegram 輪詢監聽...")
            # 注意：在已運行的 loop 中，我們手動啟動
            await tg_adapter.application.updater.start_polling()
            await tg_adapter.application.start()
            
            # 保持運行
            logger.info("💎 系統已完全就緒，進入監控狀態。")
            while True:
                await asyncio.sleep(3600)
        else:
            logger.warning("❌ 未檢測到 TELEGRAM_BOT_TOKEN，進入 CLI 閒置模式。")
            while True:
                await asyncio.sleep(3600)
                
    except Exception as e:
        logger.critical(f"💥 發生嚴重錯誤: {e}", exc_info=True)
        await asyncio.sleep(10)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
