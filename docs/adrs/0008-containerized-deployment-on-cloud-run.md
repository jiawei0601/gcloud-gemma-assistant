# ADR 0008: Containerized Deployment on Cloud Run

## 狀態 (Status)
Accepted

## 背景 (Context)
`gcloud-gemma-assistant` 需要一個高可用、易於擴展且低維護成本的執行環境。由於助理主要由 Telegram Bot 驅動，且涉及長耗時的研究任務，部署環境必須能處理長時間的連線或非同步任務。

## 決策 (Decision)
我們決定將應用程式容器化，並部署至 **Google Cloud Run**。

1. **容器化**：使用 Docker 進行封裝，確保開發與生產環境一致。
2. **託管服務**：選擇 Cloud Run (Managed)，利用其自動縮放與無需管理基礎設施的優勢。
3. **安全注入**：透過 **Google Cloud Secret Manager** 注入敏感資訊（如 `TELEGRAM_BOT_TOKEN`），避免憑證外洩。
4. **權限控制**：為 Cloud Run 設定專用的 Service Account，並僅授權必要的 Vertex AI、Storage 與 Secret Manager 存取權限。

## 限制與政策 (Policies)
1. **最小化映像檔**：使用 `python:slim` 基礎映像檔並採用多階段編譯 (Multi-stage build)。
2. **非 Root 執行**：容器內以 `appuser` 身分運行，降低安全風險。
3. **無狀態化**：應用程式本身保持無狀態，所有的持久化資料均存放於 Firestore 或 Google Drive。

## 後果 (Consequences)

### 優點 (Pros)
* **自動縮放**：可根據請求量自動調整實例數量。
* **低運運維成本**：由 Google 全面代管補丁與更新。
* **安全性**：利用 GCP 原生安全工具進行權限控管。

### 缺點 (Cons)
* **Cold Start**：Cloud Run 實例冷啟動時可能會有些微延遲。
* **長連線處理**：Telegram Polling 模式在 Cloud Run 上需開啟「CPU Always Allocated」功能，或需轉換為 Webhook 模式以達成最佳成本效益。
