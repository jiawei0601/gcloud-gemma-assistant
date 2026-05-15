# ADR 0006: Discovery Strategy and Scraping Policy

## 狀態 (Status)
Accepted

## 背景 (Context)
AI 助理需要即時的網路資訊來補充其訓練數據的不足（Cutoff Date）。我們需要一個穩健的機制來從網路上「探索」並擷取最新資訊，並將其彙整為模型的 Context。

## 決策 (Decision)
我們決定實施一個具有「深層模組 (Deep Module)」特性的 **Discovery Engine**：
1. **搜尋策略 (Search Strategy)**：優先使用 **Google Custom Search API** 獲取高相關性的 URL。
2. **抓取策略 (Scraping Strategy)**：使用 `httpx` 進行非同步請求，並結合 `BeautifulSoup` 進行 HTML 清洗。
3. **抽象化 (Abstraction)**：Orchestrator 不應感知搜尋 API 或 HTML 解析的細節。Discovery Engine 僅暴露簡單的 `fetch_information(query)` 介面。

## 限制與政策 (Constraints & Policies)
1. **Token 管理**：Discovery Engine 負責對抓取的文本進行初步截斷（例如 5000 字元），以防止 Context Window 溢出。
2. **禮貌爬取**：使用標準 User-Agent，並透過限制併發請求數來減輕目標伺服器負擔。
3. **成本控制**：單次研究任務的搜尋請求限制在 5 筆結果以內。
4. **容錯機制**：若單一 URL 抓取失敗，引擎應繼續處理後續結果，而不應中斷整個流程。

## 後果 (Consequences)

### 優點 (Pros)
* **模組解耦**：Orchestrator 保持簡潔，未來可輕易更換搜尋供應商（如 Bing 或 DuckDuckGo）。
* **資料純淨**：Discovery Engine 會過濾掉導覽列、頁尾等噪音，僅提供高品質內容。

### 缺點 (Cons)
* **延遲增加**：外部網路請求會增加整體任務的執行時間。
* **API 成本**：Google Custom Search API 超過免費額度後會產生費用。
