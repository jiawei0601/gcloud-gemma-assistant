# ADR 0002: Abstraction of Intelligence Module and Gemma 4 Integration

## 狀態 (Status)
Accepted

## 背景 (Context)
本專案要求所有模型調用均使用 **Gemma 4 26B**。為了確保系統的可維護性，並在未來可能升級模型時降低重構成本，需要對智能邏輯進行封裝。

## 決策 (Decision)
1. 實作 **Intelligence Module** 作為 Deep Module，封裝所有與 Gemma 4 26B 互動的細節。
2. 採用 **Provider Pattern**：定義統一的 `InferenceService` 介面，隱藏具體的 Prompt 模板與 Token 處理邏輯。
3. 確保 Prompt 模板與業務邏輯分離，並集中管理於 Intelligence Module 內部。

## 後果 (Consequences)

### 優點 (Pros)
*   **模組解耦**: 其他模組（如 Core）僅需傳送「資訊碎片」給 Intelligence Module，不需關心 LLM 的具體實作。
*   **模型一致性**: 確保所有任務都遵循相同的推理邏輯與 Gemma 4 優化參數。
*   **易於測試**: 可以輕易 Mock 整個 Intelligence Module 進行端對端測試。

### 缺點 (Cons)
*   **抽象層開銷**: 增加了一層調用深度。
*   **參數固定化**: 對於特定場景可能需要更靈活的 Prompt 調整，這需要在介面設計時考慮適度的配置化。
