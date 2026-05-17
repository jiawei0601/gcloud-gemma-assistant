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

## 🛠️ 從零開始部署完整流程 (Step-by-Step Guide)

請按照以下五個階段，從最乾淨的環境開始，在 15 分鐘內完成整套系統的雲端部署：

### 🏁 階段一：準備工作與環境配置

1. **建立 GCP 專案**：
   - 前往 [Google Cloud Console](https://console.cloud.google.com/)。
   - 點擊左上方專案下拉選單，建立一個新專案，並記錄您的 **專案 ID** (例如：`logical-contact-496003-p1`)。
2. **啟用必備 GCP API**：
   - 前往 API 庫頁面，搜尋並**啟用**以下 API：
     - **Vertex AI API**
     - **Cloud Run API**
     - **Secret Manager API**
     - **Custom Search API** (搜尋整個網路用)
3. **安裝本地 GCP 終端 CLI (`gcloud`)**：
   - 下載並安裝 [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)。
   - 在您的 PowerShell 中執行 `gcloud init`，登入您的 GCP 帳號並選定您剛建立的專案 ID。
4. **申請 Telegram 機器人**：
   - 在 Telegram 搜尋 [@BotFather](https://t.me/botfather)，發送 `/newbot` 指令。
   - 依照指示命名機器人，並複製取得的 **Telegram Bot Token** (例如：`8666659841:AAHE2...`)。

---

### 🔑 階段二：安全金鑰配置 (Secret Manager)

為了保護敏感的金鑰資訊，本專案強制要求將所有密鑰存放在 Google Secret Manager 中：

1. **Telegram 機器人金鑰**：
   - 在 Secret Manager 中建立一個名為 **`TELEGRAM_BOT_TOKEN`** 的密鑰，將您的 Telegram Bot Token 作為密鑰值寫入。
2. **Google 搜尋金鑰**：
   - 前往 GCP 憑證頁面，建立一個 **API 金鑰**，並在 Secret Manager 中存為 **`GOOGLE_SEARCH_API_KEY`**。
3. **Google 搜尋 CX ID**：
   - 前往 [Programmable Search Engine](https://programmablesearchengine.google.com/)，建立一個搜尋整個網路的搜尋引擎，取得其 **CX ID**，並在 Secret Manager 中存為 **`GOOGLE_SEARCH_CX`**。

---

### 📂 階段三：個人 Google Drive 驗證 (破解 0MB 限制)

由於 Google 服務帳戶的雲端硬碟儲存配額為 **0MB**，我們必須在雲端掛載個人帳戶的驗證 Token：

1. **建立 OAuth 用戶端密鑰**：
   - 在 GCP Console 進入「API 和服務」 > 「憑證」。
   - 點擊「建立憑證」 > 「OAuth 用戶端 ID」，應用程式類型選擇 **「桌面應用程式 (Desktop App)」**。
   - 建立後下載 JSON 格式的金鑰檔案，將其重新命名為 **`credentials.json`**，並直接放置於本專案的根目錄下。
2. **執行本地驗證與上傳腳本**：
   - 在專案目錄下執行以下指令安裝依賴並運行驗證：
     ```powershell
     pip install google-auth-oauthlib google-auth
     python auth_helper.py
     ```
   - 腳本會自動引導您在瀏覽器完成個人帳號的 Google 授權，並在本地生成 `token.json`。
   - 隨後，腳本會自動呼叫您的 `gcloud` CLI，將 `token.json` 安全上傳並儲存至 Secret Manager，命名為 **`GOOGLE_DRIVE_TOKEN`**。

---

### 🛡️ 階段四：IAM 服務帳戶權限設定

為了讓 Cloud Run 的無頭容器能安全讀取 Secret Manager 的密鑰與讀寫 Firestore：

1. **獲取 Cloud Run 服務帳戶**：
   - 預設情況下，Cloud Run 會使用專案的預設服務帳戶，格式為：
     `927751279284-compute@developer.gserviceaccount.com` (其中 `927751279284` 為您的專案編號)。
2. **授予必備 IAM 角色**：
   - 前往 GCP Console 的 **IAM 和管理員** 頁面。
   - 編輯您的 Cloud Run 服務帳戶，為其**新增**以下兩個角色：
     - **Secret Manager 密鑰存取者 (Secret Manager Secret Accessor)**
     - **Datastore 用戶 (Datastore User)** (此為 Firestore 原生模式讀寫所需之權限)

---

### 🚀 階段五：一鍵指令部署至 Cloud Run

請將以下部署命令中的 `您的專案ID` 替換為實際的 ID，然後在專案根目錄下直接執行：

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

> [!IMPORTANT]
> **防覆蓋掛載路徑**：
> 在上述命令中，我們將個人授權 `GOOGLE_DRIVE_TOKEN` 掛載到了獨立的安全目錄 `/secrets/token.json`。這項防禦性配置完美避開了將密鑰直接掛載在 `/app` 目錄導致 Kubernetes 覆蓋並清空原有專案代碼的致命當機錯誤。

---

### 🎬 階段六：設定共享存放資料夾與實測

1. **建立專屬存放資料夾**：
   - 在您個人的 Google Drive 建立一個新資料夾（例如命名為 `AG`）。
   - 點擊「共用」，將此資料夾權限分享給機器人助理的服務帳戶（例如：`927751279284-compute@developer.gserviceaccount.com`），並務必將權限設為 **「編輯者 (Editor)」**。
2. **複製資料夾 ID 並設定程式碼鎖定**：
   - 開啟您的共享資料夾，從網址列複製其資料夾 ID (網址格式為：`drive.google.com/drive/folders/資料夾ID`)。
   - 在專案的 [google_drive_provider.py](file:///c:/Users/chang/OneDrive/Documents/AG/gcloud-gemma-assistant/src/delivery/google_drive_provider.py#L16-L23) 中，將 `target_folder_id` 修改為您的共享資料夾 ID，以鎖定存放路徑：
     ```python
     async def _find_shared_folder_id(self) -> Optional[str]:
         # 將此處 ID 替換為您的共享資料夾 ID
         target_folder_id = "您的共享資料夾ID"
         return target_folder_id
     ```
   - 重新部署 Cloud Run 後即可完成綁定！
3. **Telegram 機器人實測**：
   - 在 Telegram 開啟與您的機器人的對話。
   - 發送 `/start` 啟動機器人。
   - 發送指令：💬 **「新增一個sheet，檔案名稱是TEST，A1是今天的日期，B1是現在的時間」**。
   - 機器人將秒速在資料夾內建立試算表、JSON化傳輸寫入日期時間，並優雅回傳可分享的檢視連結！

---

## 📂 檔案結構與核心技術特徵

- `bot.py`：Flask Webhook 進入點 (異步 Queue + 多執行緒去重機制，無狀態容器部署最佳實踐)。
- `auth_helper.py`：全自動本地個人 OAuth2 授權與 Secret Manager 同步輔助腳本。
- `config.py`：全域配置與環境變數管理。
- `src/clients/gemini_client.py`：
  - **JSON 結構化傳回值**：為 Docs 與 Sheets 工具設計結構化 JSON 字串傳回值，杜絕模型解析錯誤。
  - **二維 JSON 參數解碼**：將 `update_google_sheet` 修改為 `values_json: str`，完美避開 Gemini 後端不支援二維 Nested Array Schema 的底層限制。
- `src/delivery/engine.py`：安全載入機制。優先讀取 `/secrets/token.json`，若無則自動 Fallback 到 `google.auth.default` (ADC)。
- `src/delivery/google_drive_provider.py`：**精準目錄鎖定**。強制將 `_find_shared_folder_id` 鎖定為使用者指定的資料夾 ID，確保隱私安全與歸檔整潔。
- `src/communication/handlers.py`：專家小組人設、任務邏輯與背景待辦事項提取器。
- `Dockerfile`：生產級容器化配置。

---
**免責聲明**：此助理產出之資訊僅供參考，投資與決策請審慎評估。
