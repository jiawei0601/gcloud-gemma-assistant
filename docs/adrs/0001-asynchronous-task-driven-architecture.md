# ADR 0001: Asynchronous Task-Driven Architecture

## 狀態 (Status)
Accepted

## 背景 (Context)
在執行網路搜尋與 Gemma 4 26B 的深度推理時，系統面臨以下挑戰：
1. **高延遲 (High Latency)**: 爬取多個網頁並進行 26B 模型的長文本彙整通常需要數分鐘，遠超 HTTP 同步請求的超時限制。
2. **資源成本**: LLM 推理與網頁抓取是計算密集型工作，需要有效的隊列管理以防止系統過載。

## 決策 (Decision)
我們決定採用 **非同步任務驅動架構 (Asynchronous Task-Driven Architecture)**：
1. 使用 **Google Cloud Tasks** 作為任務排隊與調度器。
2. 當 API 接收到 `Research Task` 請求後，立即返回 `TaskID`，並將具體工作異步分發。
3. 使用 **Firestore** 紀錄任務狀態（`PENDING`, `SEARCHING`, `SYNTHESIZING`, `COMPLETED`, `FAILED`）。

## 後果 (Consequences)

### 優點 (Pros)
*   **使用者體驗**: 使用者不需等待連線直到逾時，可隨時透過 ID 查詢進度。
*   **穩定性**: 具備自動重試機制，且可控制並發處理數量，避免觸發 API Quota 限制。
*   **擴展性**: 易於水平擴展工作節點以處理更多併發任務。

### 缺點 (Cons)
*   **複雜度**: 需額外維護狀態存儲與異步隊列的邏輯。
*   **延遲回饋**: 客戶端需實作 Poll 或 Webhook 來獲取最終產出。
