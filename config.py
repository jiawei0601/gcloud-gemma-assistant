import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "logical-contact-496003-p1")
    # 優先讀取環境變數，若無則預設為 us-central1
    LOCATION: str = os.environ.get("GCP_LOCATION", "us-central1") 
    # 優先讀取環境變數，若無則預設為 gemini-2.5-pro
    GEMINI_MODEL_ID: str = os.environ.get("GEMINI_MODEL_ID", "gemini-2.5-pro")
    TELEGRAM_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    PORT: int = int(os.environ.get("PORT", 8080))
    WEBHOOK_URL: str = os.environ.get("WEBHOOK_URL", "")

config = Config()
