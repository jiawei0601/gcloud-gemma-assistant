# ADR 0004: Telegram as User Interface

## 狀態 (Status)
Accepted

## 背景 (Context)
`gcloud-gemma-assistant` 專案目前缺乏一個面向使用者的互動介面。雖然核心引擎（Orchestrator）可以執行複雜的研究任務，但使用者需要一種便捷的方式來觸發任務並接收報告，尤其是在遠端或移動設備上。

我們需要一個輕量、支援推送通知且易於使用的介面，而無需開發複雜的 Web 前端。

## 決策 (Decision)
我們決定實施 **Telegram Bot 適配器** 作為主要的用戶介面。

具體實施細節：
1. **通訊模組 (`src/communication`)**: 建立專用的模組來處理 Telegram Bot API 的溝通。
2. **適配器模式 (Adapter Pattern)**: 該模組僅負責將 Telegram 的指令轉換為內部系統可理解的 `ResearchTask` 指令，不包含業務邏輯。
3. **異步支持**: 使用 `python-telegram-bot` (v20+) 程式庫，這與我們目前的非同步架構完全一致。

## 後果 (Consequences)

### 優點 (Pros)
* **開發成本低**: 無需建立 Web Server 或前端介面。
* **原生推送通知**: 使用者在研究任務完成時能立即收到通知。
* **跨平台**: 使用者可透過電腦或手機的 Telegram 應用程式隨時隨地發起研究。

### 缺點 (Cons)
* **第三方依賴**: 系統的可用性部分取決於 Telegram 服務的穩定性。
* **安全管理**: 必須妥善保管 Bot Token。
* **介面受限**: 主要限於文字與 Markdown 互動，缺乏豐富的 UI 元件。

## 合規性 (Compliance)
所有的輸入必須經過 `CommandHandler` 的驗證後才能傳遞給 `Orchestrator`。
