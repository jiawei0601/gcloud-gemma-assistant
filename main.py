import asyncio
import logging
import os
import http.server
import threading
import sys
import json
from dotenv import load_dotenv

# 強制刷新 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
load_dotenv()

# 配置全局日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("Main")

# 全域變數供 Webhook 使用
tg_adapter = None

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # 健康檢查路徑
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_POST(self):
        # Telegram Webhook 進入點
        if self.path == "/telegram":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            update_json = json.loads(post_data.decode('utf-8'))
            
            # 非同步處理更新
            if tg_adapter:
                asyncio.run_coroutine_threadsafe(
                    tg_adapter.process_update(update_json), 
                    main_loop
                )
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args): return

def run_http_server():
    port = int(os.getenv("PORT", "8080"))
    server_address = ('0.0.0.0', port)
    httpd = http.server.HTTPServer(server_address, WebhookHandler)
    logger.info(f"✅ [SYSTEM] Webhook 伺服器啟動於 0.0.0.0:{port}")
    httpd.serve_forever()

async def start_bot():
    global tg_adapter, main_loop
    main_loop = asyncio.get_running_loop()
    
    logger.info("🎬 [SYSTEM] 啟動初始化流程 (Webhook 模式)...")
    
    try:
        from src.core.orchestrator import Orchestrator
        from src.intelligence.factory import IntelligenceFactory
        from src.communication.telegram_adapter import TelegramAdapter
        
        intelligence_svc = IntelligenceFactory.create_provider()
        orchestrator = Orchestrator(intelligence_provider=intelligence_svc)
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        admin_id = os.getenv("ADMIN_CHAT_ID")
        # Cloud Run 的外部 URL，由環境變數提供
        webhook_url = os.getenv("WEBHOOK_URL", f"https://gemma-assistant-927751279284.asia-east1.run.app")
        
        if not bot_token:
            logger.error("❌ [BOT] TELEGRAM_BOT_TOKEN 缺失！")
            return

        tg_adapter = TelegramAdapter(bot_token, orchestrator)
        await tg_adapter.initialize()
        
        # 啟動 Webhook 模式
        await tg_adapter.run_webhook(webhook_url, int(os.getenv("PORT", "8080")))
        
        # 啟動 HTTP Server (處理健康檢查與 Webhook)
        threading.Thread(target=run_http_server, daemon=True).start()
        
        if admin_id:
            await tg_adapter.send_startup_notification(admin_id)
            
        logger.info("💎 [SYSTEM] Webhook 模式已就緒。")
        while True:
            await asyncio.sleep(3600)
                
    except Exception as e:
        logger.critical(f"💥 [FATAL] 啟動失敗: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("👋 [SYSTEM] 程式終止。")