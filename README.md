# 🚀 Gemini 2.5 Pro 多代理人研究助理 (Cloud Run 版)

這是一個基於 **Google Gemini 2.5 Pro** 與 **Vertex AI** 構建的進階研究助理。它採用了「分析師團隊」架構，具備聯網搜尋能力，能針對特定主題產出專業的研究報告，也支援日常的互動式資訊查找。

## 🌟 核心特色
- **多代理人協作 (Multi-Agent)**：自動指派數據員、分析師、評估師與總編進行深度交叉分析。
- **即時聯網 (Google Search)**：整合 Google 搜尋工具，確保獲取 2026 年最新資訊。
- **無狀態架構**：針對 Cloud Run 優化，徹底解決 Event Loop 衝突與 404 報錯。
- **全球穩定路由**：推理核心鎖定 `us-central1` 以獲取最高穩定性與最新模型功能。

---

## 🛠️ 環境變數與金鑰申請流程

部署此助理需要以下 6 個關鍵變數。請按照以下流程申請：

### 1. Telegram Bot Token (`TELEGRAM_BOT_TOKEN`)
- **申請方法**：
    1. 在 Telegram 搜尋 [@BotFather](https://t.me/botfather)。
    2. 發送 `/newbot` 指令並按照指示命名。
    3. 取得 API Token (格式如：`123456:ABC-DEFG...`)。

### 2. Google Search API Key (`GOOGLE_SEARCH_API_KEY`)
- **申請方法**：
    1. 前往 [Google Cloud Console](https://console.cloud.google.com/)。
    2. 搜尋並啟用 **"Custom Search API"**。
    3. 在「憑證」頁面建立一個 **API 金鑰**。

### 3. Google Search CX ID (`GOOGLE_SEARCH_CX`)
- **申請方法**：
    1. 前往 [Programmable Search Engine](https://programmablesearchengine.google.com/)。
    2. 建立一個新的搜尋引擎，選擇「搜尋整個網路」。
    3. 在「基本設定」中複製 **搜尋引擎 ID** (CX)。

### 4. GCP 專案 ID (`GCP_PROJECT_ID`)
- **申請方法**：
    1. 在 GCP Console 首頁上方導覽列查看目前選定的專案名稱旁的 ID (如：`logical-contact-496003-p1`)。

### 5. Webhook 網址 (`WEBHOOK_URL`)
- **設定方法**：
    1. 此為您的 Cloud Run 服務部署後的網址 (格式如：`https://gemma-assistant-xxxx.a.run.app`)。
    2. 首次部署後取得網址，再更新環境變數。

### 6. 模型 ID (`GEMINI_MODEL_ID`)
- **建議值**：`gemini-2.5-pro` (強大研究用) 或 `gemini-1.5-flash-002` (快速反應用)。

---

## 🚀 部署步驟

### 步驟一：開啟 Vertex AI API
在 GCP Console 搜尋 **Vertex AI** 並點擊「啟用所有建議的 API」。

### 步驟二：配置 Secret Manager (強烈建議)
為了安全起見，請將 `TELEGRAM_BOT_TOKEN`, `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_CX` 存入 **Secret Manager**，並在部署時引用。

### 步驟三：使用 gcloud 指令部署
在專案根目錄執行以下指令：

```powershell
gcloud run deploy gemma-assistant `
  --source . `
  --region asia-east1 `
  --project=您的專案ID `
  --allow-unauthenticated `
  --set-env-vars="GCP_PROJECT_ID=您的專案ID,GCP_LOCATION=us-central1,GEMINI_MODEL_ID=gemini-2.5-pro,WEBHOOK_URL=您的服務網址" `
  --set-secrets="TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest,GOOGLE_SEARCH_API_KEY=GOOGLE_SEARCH_API_KEY:latest,GOOGLE_SEARCH_CX=GOOGLE_SEARCH_CX:latest"
```

---

## 📖 指令說明
- `/start`：啟動助理並查看功能清單。
- `/research <主題>`：啟動多代理人專家團隊，產出深度研究報告。
- **直接輸入文字**：助理會使用 Google 搜尋回答您的問題。

---

## 📂 檔案結構
- `bot.py`：Flask Webhook 進入點 (無狀態處理)。
- `config.py`：全域配置與環境變數管理。
- `src/clients/gemini_client.py`：Gemini SDK 同步封裝。
- `src/communication/handlers.py`：專家小組人設與任務邏輯。
- `Dockerfile`：生產級容器化配置。

---
**免責聲明**：此助理產出之資訊僅供參考，投資與決策請審慎評估。
