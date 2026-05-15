# ADR 0007: Delivery Strategy and Google Ecosystem Integration

## 狀態 (Status)
Accepted

## 背景 (Context)
助理生成的報告需要一個持久化且易於存取的儲存空間。使用者要求整合 Google Drive 與 Docs，以便在研究完成後直接進行後續編輯與協作。

直接在核心邏輯中呼叫 Google API 會導致程式碼與特定雲端服務強耦合，且難以處理複雜的身份驗證、重試機制與格式轉換。

## 決策 (Decision)
我們決定實施一個具備「深層模組 (Deep Module)」特性的 **Delivery Engine**：
1. **介面驅動 (Interface-Driven)**：定義 `BaseDeliveryProvider` 抽象介面，Orchestrator 僅與此介面溝通。
2. **引擎封裝 (Engine Abstraction)**：建立 `GoogleDeliveryEngine` 負責處理所有「底層作業」（如 OAuth2 認證、Token 刷新、重試邏輯、MIME 類型轉換）。
3. **單一職責 (Separation of Concerns)**：
    * **Provider 層**：負責業務邏輯，例如「將 Markdown 轉換為 HTML 以便 Google Docs 轉換」。
    * **Engine 層**：負責通訊協定與 API 穩定性。

## 限制與政策 (Policies)
1. **格式自動轉換**：交付模組應能自動將純文本或 Markdown 轉換為 Google Docs 格式。
2. **權限管理**：產出的檔案預設設為「連結分享者可讀 (Anyone with link)」，並回傳 `webViewLink` 給使用者。
3. **重試機制**：針對 429 (Too Many Requests) 或 503 等暫時性錯誤實作指數退避 (Exponential Backoff)。

## 後果 (Consequences)

### 優點 (Pros)
* **可測試性**：可以輕易透過 Mock Provider 進行研究流程測試，無需真實 Google 憑證。
* **擴展性**：未來若需支援其他儲存服務（如 S3 或 Dropbox），只需實作新的 Provider。
* **強韌性**：重試機制集中管理，確保上層邏輯不被網路波動干擾。

### 缺點 (Cons)
* **架構複雜度**：增加了模組分層的深度。
* **憑證管理**：需妥善管理 `credentials.json` 與 `token.json`。
