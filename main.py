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
# 同時配置 root logger 以捕捉所有庫的日誌
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("Main")

logger.info("🎬 [SYSTEM] 程式入口啟動...")

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
    logger.info(f"✅ [HEALTH] 伺服器已就緒: 0.0.0.0:{port}")
    httpd.serve_forever()

threading.Thread(target=run_health_check_server, daemon=True).start()

async def start_bot():
    logger.info("🚀 [BOT] 正在初始化非同步核心...")
    
    try:
        from src.core.orchestrator import Orchestrator
        from src.intelligence.factory import IntelligenceFactory
        from src.communication.telegram_adapter import TelegramAdapter
        
        intelligence_svc = IntelligenceFactory.create_provider()
        orchestrator = Orchestrator(intelligence_provider=intelligence_svc)
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        admin_id = os.getenv("ADMIN_CHAT_ID")
        
        if not bot_token:
            logger.error("❌ [BOT] TELEGRAM_BOT_TOKEN 缺失！")
            return

        logger.info(f"🤖 [BOT] 正在嘗試連線 (Token 長度: {len(bot_token)})")
        tg_adapter = TelegramAdapter(bot_token, orchestrator)
        
        # 1. 初始化
        await tg_adapter.initialize()
        
        # 2. 驗證身份 (極其重要，確認 Token 有效性與網路)
        me = await tg_adapter.application.bot.get_me()
        logger.info(f"✅ [BOT] 連線成功！機器人名稱: @{me.username}")
        
        # 3. 發送通知
        if admin_id:
            logger.info(f"🔔 [BOT] 發送啟動通知至: {admin_id}")
            await tg_adapter.send_startup_notification(admin_id)
            
        # 4. 啟動並保持運行
        logger.info("📡 [BOT] 開始監聽指令...")
        async with tg_adapter.application:
            await tg_adapter.application.start()
            await tg_adapter.application.updater.start_polling()
            # 保持運行直到收到訊號
            while True:
                await asyncio.sleep(3600)
                
    except Exception as e:
        logger.critical(f"💥 [FATAL] 啟動崩潰: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("👋 [SYSTEM] 程式手動關閉。")
