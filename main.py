import asyncio
import logging
import os
import http.server
import threading
import sys
from dotenv import load_dotenv

# 強制刷新 stdout
sys.stdout.reconfigure(line_buffering=True)
load_dotenv()

# 配置全局日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("Main")

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args): return

def run_health_check_server():
    port = int(os.getenv("PORT", "8080"))
    server_address = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(server_address, HealthCheckHandler)
    logger.info(f"✅ [HEALTH] 伺服器啟動於 0.0.0.0:{port}")
    httpd.serve_forever()

async def start_bot():
    logger.info("🎬 [SYSTEM] 啟動初始化流程...")
    
    try:
        # 分步載入模組，以便追蹤進度
        logger.info("📦 [LOAD] 正在載入核心協調器...")
        from src.core.orchestrator import Orchestrator
        
        logger.info("📦 [LOAD] 正在載入智慧引擎...")
        from src.intelligence.factory import IntelligenceFactory
        
        logger.info("📦 [LOAD] 正在載入 Telegram 轉接器...")
        from src.communication.telegram_adapter import TelegramAdapter
        
        logger.info("⚙️ [INIT] 正在初始化服務組件...")
        intelligence_svc = IntelligenceFactory.create_provider()
        orchestrator = Orchestrator(intelligence_provider=intelligence_svc)
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        admin_id = os.getenv("ADMIN_CHAT_ID")
        
        if not bot_token:
            logger.error("❌ [BOT] TELEGRAM_BOT_TOKEN 缺失！")
            return

        logger.info(f"🤖 [BOT] 正在建立連線 (Token: {bot_token[:10]}...)")
        tg_adapter = TelegramAdapter(bot_token, orchestrator)
        
        # 初始化與身份驗證
        await tg_adapter.initialize()
        me = await tg_adapter.application.bot.get_me()
        logger.info(f"✅ [BOT] 驗證成功: @{me.username}")
        
        # 啟動背景健康檢查伺服器 (僅在 Bot 驗證成功後)
        logger.info("📡 [SYSTEM] 啟動健康檢查伺服器...")
        threading.Thread(target=run_health_check_server, daemon=True).start()
        
        if admin_id:
            logger.info(f"🔔 [BOT] 發送啟動通知...")
            await tg_adapter.send_startup_notification(admin_id)
            
        logger.info("💎 [SYSTEM] 系統已全面就緒，開始輪詢監聽。")
        async with tg_adapter.application:
            await tg_adapter.application.start()
            await tg_adapter.application.updater.start_polling()
            while True:
                await asyncio.sleep(3600)
                
    except Exception as e:
        logger.critical(f"💥 [FATAL] 啟動失敗: {e}", exc_info=True)
        # 在失敗時也要開啟埠口，否則 Cloud Run 會一直無限重啟而看不到完整日誌
        threading.Thread(target=run_health_check_server, daemon=True).start()
        await asyncio.sleep(300)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(start_bot())
