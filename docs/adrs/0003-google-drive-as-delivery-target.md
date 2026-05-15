# ADR 0003: Google Drive as Primary Delivery Target

## 狀態 (Status)
Accepted

## 背景 (Context)
研究報告產出後需要一個持久且易於分享的存放空間。使用者要求將結果存放在 Google Drive 的指定資料夾，並使用 Doc 或 Sheet 格式。

## 決策 (Decision)
1. 實作 **Delivery Module**，專門負責處理 Google Ecosystem 的寫入工作。
2. 使用 **Google Drive API** 進行資料夾定位與權限確認。
3. 使用 **Google Docs API** 生成敘述性報告，使用 **Google Sheets API** 生成結構化資料表。
4. 所有的交付過程均回報該產出物的 `FileID` 與 `WebViewLink` 給 Orchestrator。

## 後果 (Consequences)

### 優點 (Pros)
*   **整合性**: 直接融入使用者的日常工作流。
*   **安全性**: 利用 Google 原生的 IAM 與共用連結管理。
*   **版本控制**: Google Drive 自帶版本紀錄功能。

### 缺點 (Cons)
*   **OAuth 複雜度**: 需處理認證刷新（Refresh Tokens）與服務帳戶（Service Account）權限。
*   **格式轉換**: 需精確處理 Markdown 或純文字到 Google Docs 格式的轉換。
