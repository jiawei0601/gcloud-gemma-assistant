# 🛠️ CLAUDE.md — AI 助理開發規範與基礎邏輯

此文件定義了 AI 助理（如 Antigravity, Claude Code 等）在開發本倉庫時**必須嚴格遵守**的開發規範、基礎邏輯與常用指令。

---

## 🧠 AI 助理基礎邏輯與約束 (Base Logic & Constraints)

本專案已全面導入 **AI 智能編程技能庫**（位於 `.claude/skills/` 內）。AI 助理在啟動任務時，必須將這些技能視為**最高優先級的基礎推理邏輯**：

### 🚨 核心工作流程約束 (Critical Workflow Constraint)
在收到任何開發、重構或修復需求時，AI 助理**絕對禁止直接編寫或修改程式碼**。必須嚴格遵循以下步驟：
1. **詳細需求對齊**：主動啟動 `/grill-with-docs` 技能，就業務目的、架構依賴、邊界情況向開發者提出深度詢問。
2. **提出設計方案**：整理需求後，給出一個詳盡的技術方案，包含：
   * 系統架構影響分析。
   * 資料流與模組調用圖（使用 Mermaid）。
   * 實作計畫與預計改動的檔案列表。
3. **方案簽核**：將方案呈現給開發者，並明確詢問：「此方案是否符合您的預期？請回覆『確認』，我將在您的授權下正式開始作業。」
4. **開始作業**：**僅在收到開發者明確的「確認」或「同意」回覆後，才可動筆撰寫第一行程式碼**。在作業過程中，依據功能屬性主動配合 `/tdd`、`/diagnose` 或 `/vertical-slice` 進行小步迭代。

---

## 📦 專案常用指令 (Common Commands)

### 1. 環境與依賴
* **安裝依賴套件**：
  ```powershell
  pip install -r requirements.txt
  ```

### 2. 執行服務
* **本地啟動 Telegram 機器人 (Bot)**：
  ```powershell
  python bot.py
  ```
* **本地啟動主服務 (Flask Webhook)**：
  ```powershell
  python main.py
  ```

### 3. 測試與驗證
* **執行單體測試**（如有補上）：
  ```powershell
  pytest
  ```

---

## 📐 程式碼風格與架構準則
* **命名規範**：變數與函式使用 `snake_case`，類別使用 `PascalCase`。
* **類型標註**：所有新撰寫的 Python 程式碼應儘可能加上 Python Type Hints，提升程式碼健壯度。
* **架構風格**：遵循模組化、單一職責原則（Single Responsibility Principle）。各層級（Clients, Communication, Shared）職責分明，禁止在 shared 中寫入業務邏輯。
