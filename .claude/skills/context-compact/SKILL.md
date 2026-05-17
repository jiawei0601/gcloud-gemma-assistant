---
name: context-compact
description: 將長對話或複雜的開發階段壓縮為精煉的 CONTEXT.md 與 HANDOFF.md，以便於下次繼續。適用於對話長度接近 Token 限制、或需要交接給新階段時。
---

# 📦 對話上下文壓縮與交接技能 (`context-compact`)

在長期的編程對話中，隨著時間推移，對話上下文會累積大量的冗餘訊息、偵錯嘗試與無關雜訊。這不僅會導致 AI 助理反應變慢，還會耗費龐大的 Token 費用，甚至讓 AI 開始產生幻覺或忘記初衷。

此技能引導 AI 助理在適當時機，將所有混亂的對話歷史壓縮為精鍊的「交接包（Handoff Package）」，確保下一輪對話能夠無縫接軌。

---

## 📋 觸發警示 (Trigger Warning)

當發生以下情況時，AI 助理**應主動建議**執行此技能：
1. **對話長度極長**，已經歷多次偵錯、重構與代碼修改。
2. 開發者提到：「我們今天先到這裡，明天繼續」或「我需要開啟一個新對話」。
3. 準備將任務從一個 Agent（如程式碼實作 Agent）交接給另一個 Agent（如部署 Agent）。

---

## 🚀 上下文壓縮流程步驟

當啟用 `/context-compact` 技能時，AI 助理**必須**執行以下步驟：

### 📋 步驟 1：整理並盤點變更 (Diff Inventory)
* 調用 Git 工具，列出在此次對話中所有**新增、修改、刪除**的檔案。
* 總結這段時間內所做的關鍵技術決策（例如：「我們選擇使用 Firestore Transaction 來解決併發寫入問題」）。

### 📝 步驟 2：建立或更新 `HANDOFF.md`
在專案根目錄（或交接目錄下）建立或覆寫 [HANDOFF.md](file:///c:/Users/chang/OneDrive/Documents/AG/HANDOFF.md)。該檔案應具備極度精煉、無廢話的結構，內容包括：

1. **🎯 任務當前狀態 (Current State)**
   - 目前專案進度到哪裡了？
   - 哪些功能已通過測試並部署？
2. **🏗️ 核心架構決策 (Architectural Decisions)**
   - 記錄在對話中達成的設計共識、資料庫 schema 變更、或使用的特殊演算法。
3. **📋 未完待辦事項 (Remaining Tasks)**
   - 接下來需要實作的下一個垂直切片或步驟。
   - 待解決的潛在 Bug 或技術債。
4. **💡 新對話啟動指令 (Bootstrap Command)**
   - 提供一段給下一個 AI 助理的「首發引導語（Prompt）」，使其讀取 `HANDOFF.md` 與 `CONTEXT.md` 後能立刻進入狀況。

> [!TIP]
> 確保 `HANDOFF.md` 文字簡潔，多使用條列式（Bullet Points），避免冗長的背景描述。

### 💾 步驟 3：清理與提交 (Clean & Commit)
* 確認所有暫時性的調試檔案（如臨時的 `reproduce_*.py` 等）已被清理或妥善歸類。
* 執行 Git Commit，將當前進度保存，並在 Commit message 中註明為該階段的結束（例如：`chore: complete feature-x implementation phase & update handoff`）。

### 🤝 步驟 4：交接語句產生
* 向開發者呈獻 `HANDOFF.md` 內容。
* 輸出給開發者的交接小語，例如：
  > 「✨ 我們已成功將今天的成果打包！下次啟動新對話時，您只需對我說：
  > **『請讀取專案根目錄的 HANDOFF.md 與 CONTEXT.md，並告訴我接下來的執行步驟。』**
  > 我就會立刻以 100% 的聰明狀態繼續為您寫程式！」
