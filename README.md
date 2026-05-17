# 🚀 Gemini 2.5 Pro 多代理人研究助理 (Cloud Run 版)

這是一個基於 **Google Gemini 2.5 Pro** 與 **Vertex AI** 構建的進階研究與雲端辦公助理。它採用了「分析師團隊」架構，具備聯網搜尋與全功能 Google Drive/Docs/Sheets 整合能力，能直接在您指定的 Google Drive 資料夾中建立、寫入並修改文件與試算表。

---

## 🌟 核心特色

- **多代理人協作 (Multi-Agent)**：自動指派數據員、分析師、評估師與總編進行深度交叉分析，生成專業研究報告。
- **即時聯網 (Google Search)**：整合 Google 搜尋工具，確保獲取 2026 年最新資訊。
- **無狀態架構**：針對 Cloud Run 優化，徹底解決 Event Loop 衝突與 404 報錯。
- **全球穩定路由**：推理核心鎖定 `us-central1` 以獲取最高穩定性與最新模型功能。
- **全功能雲端辦公整合**：
  - **自動空間規避 (0MB 限制繞過)**：透過個人 OAuth2 憑證，繞過 GCP 服務帳戶預設 0MB 的空間限制。
  - **精準目錄鎖定**：自動將所有建立、上傳的 Docs 與 Sheets 文件鎖定儲存在使用者的專屬共享資料夾中。
  - **結構化 API 調用**：所有工具回傳均採用 JSON 結構化，確保模型能以 100% 精度解析檔案 ID 與可分享連結。

---

## 🔑 Google Drive / Docs / Sheets 個人化驗證配置

由於 Google 服務帳戶（Service Account）預設儲存空間為 0MB，若直接以其身份建檔會立即觸發 `storageQuotaExceeded` 錯誤。本專案透過「**個人 OAuth2 憑證掛載**」機制完美解決此問題：

### 步驟一：下載 OAuth 用戶端憑證
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)。
2. 進入「API 和服務」 > 「憑證」。
3. 建立一個 **OAuth 2.0 用戶端 ID**（類型選擇：**桌面應用程式 (Desktop App)**）。
4. 下載 JSON 格式的用戶端密鑰檔案，並將其重新命名為 **`credentials.json`**，放置於本專案的根目錄下。

### 步驟二：執行本地驗證與同步腳本
在專案根目錄下，執行我們為您設計的自動驗證腳本：
```powershell
pip install google-auth-oauthlib google-auth
python auth_helper.py
```
此腳本會：
1. 自動開啟您的瀏覽器，引導您進行個人 Google 帳號的安全授權。
2. 在本地產生帶有個人身分重新整理權談 (Refresh Token) 的 `token.json`。
3. 自動調用您本地的 `gcloud` CLI，將該 `token.json` 安全上傳並儲存至 GCP Secret Manager 的 **`GOOGLE_DRIVE_TOKEN`** 密鑰庫中。

---

## 🛠️ 環境變數與金鑰申請流程

部署此助理需要以下 7 個關鍵變數。請按照以下流程申請並配置：

| 變數名稱 | 類型 | 說明 & 申請方法 |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | **Secret** | 前往 Telegram [@BotFather](https://t.me/botfather) 創建機器人取得 |
| `GOOGLE_SEARCH_API_KEY`| **Secret** | GCP Console 啟用 Custom Search API 後建立的 API 金鑰 |
| `GOOGLE_SEARCH_CX` | **Secret** | 前往 Programmable Search Engine 建立搜尋引擎取得的 CX ID |
| `GOOGLE_DRIVE_TOKEN` | **Secret** | 由 `auth_helper.py` 本地腳本自動產生並上傳至 Secret Manager 的個人憑證 |
| `GCP_PROJECT_ID` | **Env** | 您的 GCP 專案 ID (例如：`logical-contact-496003-p1`) |
| `WEBHOOK_URL` | **Env** | Cloud Run 服務部署後的完整 HTTPS 網址 |
| `GEMINI_MODEL_ID` | **Env** | 預設為 `gemini-2.5-pro` (具備最強大的推理與複雜工具調用能力) |

---

## 🚀 部署步驟 (Cloud Run 生產環境)

### 防禦性安全掛載說明
在部署時，請將 `GOOGLE_DRIVE_TOKEN` 掛載至獨立的安全目錄 **`/secrets/token.json`**（避免直接掛載於 `/app` 目錄導致 Kubernetes 覆蓋原有專案檔案）。程式碼會自動在啟動時優先讀取此安全路徑。

在專案根目錄執行以下完整指令進行部署：

```powershell
gcloud run deploy gemma-assistant `
  --source . `
  --region asia-east1 `
  --project=您的專案ID `
  --allow-unauthenticated `
  --cpu-boost `
  --no-cpu-throttling `
  --set-env-vars="GCP_PROJECT_ID=您的專案ID,GCP_LOCATION=us-central1,GEMINI_MODEL_ID=gemini-2.5-pro,WEBHOOK_URL=您的服務網址" `
  --set-secrets="TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest,GOOGLE_SEARCH_API_KEY=GOOGLE_SEARCH_API_KEY:latest,GOOGLE_SEARCH_CX=GOOGLE_SEARCH_CX:latest,/secrets/token.json=GOOGLE_DRIVE_TOKEN:latest"
```

---

## 📖 指令與辦公功能說明

- `/start`：啟動助理並查看功能清單。
- `/research <主題>`：啟動多代理人專家團隊，產出深度研究報告。
- **直接輸入文字**：助理會使用 Google 搜尋回答您的問題。
- **辦公雲端整合**：
  - *「幫我將剛才的報告存成 DOC 放在我的雲端硬碟」*：自動在共享目錄建立 Google Doc，寫入完整內容並回傳可分享連結。
  - *「新增一個 sheet，檔案名稱是 TEST，A1 是今天的日期，B1 是現在的時間」*：自動在指定共享目錄建立 Google Sheet，透過平鋪的 JSON 格式傳輸精準寫入資料並回傳連結。

---

## 📂 檔案結構與核心技術特徵

- `bot.py`：Flask Webhook 進入點 (異步 Queue + 多執行緒去重機制)。
- `auth_helper.py`：全自動本地個人 OAuth2 授權與 Secret Manager 同步輔助腳本。
- `config.py`：全域配置與環境變數管理。
- `src/clients/gemini_client.py`：
  - **JSON 結構化傳回值**：為 Docs 與 Sheets 工具設計結構化 JSON 字串傳回值，杜絕模型解析錯誤。
  - **二維 JSON 參數解碼**：將 `update_google_sheet` 修改為 `values_json: str`，完美避開 Gemini 後端不支援二維 Nested Array Schema 的底層限制。
- `src/delivery/engine.py`：安全載入機制。優先讀取 `/secrets/token.json`，若無則自動 Fallback 到 `google.auth.default` (ADC)。
- `src/delivery/google_drive_provider.py`：**精準目錄鎖定**。強制將 `_find_shared_folder_id` 鎖定為使用者指定的資料夾 ID `1B3YXNsgDV2KesrBtrRN2QEeVO7OuWPcf`，確保隱私安全與歸檔整潔。
- `src/communication/handlers.py`：專家小組人設、任務邏輯與背景待辦事項提取器。
- `Dockerfile`：生產級容器化配置。

---
**免責聲明**：此助理產出之資訊僅供參考，投資與決策請審慎評估。
