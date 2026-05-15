# ADR 0005: Multi-Model Strategy (Gemma for Local, Gemini for Cloud)

## 狀態 (Status)
Accepted

## 背景 (Context)
為了兼顧開發測試的便利性與生產環境的強大效能，系統需要能夠在不同的運行環境下切換 AI 模型。
- **本地開發**：需要低延遲、無雲端成本且可離線運作的模型（Gemma 4 26B）。
- **雲端部屬 (Google Cloud)**：需要處理大規模、長文本且具備高推理能力的最新模型（Gemini 3.1 Flash-Lite）。

## 決策 (Decision)
我們決定實施「多模型切換策略」：
1. 建立 `IntelligenceFactory` 作為單一建立點。
2. 透過環境變數 `INTELLIGENCE_PROVIDER` 控制實體化對象。
3. 統一抽象介面，確保 `Orchestrator` 不受模型更換影響。

## 後果 (Consequences)

### 優點 (Pros)
* **成本優化**：開發時不產生雲端費用。
* **開發敏捷性**：本地開發不受網路限制，且推論速度快。
* **Gemini (Cloud)**: 作為生產級供應商，利用 Vertex AI 的擴展性處理複雜的 RAG 流程與多模態任務。採用最新發佈的 Gemini 3.1 Flash-Lite 以獲得最佳的效能與成本比。

### 缺點 (Cons)
* **行為差異**：不同模型的輸出品質與格式控制（Prompt Sensitivity）存在差異，需在抽象層進行適度調優。
* **環境配置**：需管理 GCP 認證與本地 Ollama 等多套環境。
