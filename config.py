import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "927751279284")
    LOCATION: str = os.environ.get("GCP_LOCATION", "asia-east1")
    GEMINI_MODEL_ID: str = os.environ.get("GEMINI_MODEL_ID", "gemini-3.1-pro")
    TELEGRAM_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    PORT: int = int(os.environ.get("PORT", 8080))
    WEBHOOK_URL: str = os.environ.get("WEBHOOK_URL", "")

config = Config()
