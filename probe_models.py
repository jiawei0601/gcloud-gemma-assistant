from google import genai
import os

PROJECT_ID = "logical-contact-496003-p1"
LOCATION = "asia-east1"

def list_publisher_models():
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    print(f"--- Available Models in {LOCATION} ---")
    try:
        # 獲取所有可用的基礎模型
        for model in client.models.list():
            print(f"Model ID: {model.name} | Display Name: {model.display_name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_publisher_models()
