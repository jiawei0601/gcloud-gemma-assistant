# Gemma AI Research Assistant

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-Deep--Modules-green.svg)
![AI-Model](https://img.shields.io/badge/AI--Model-Gemma--4--26B-orange.svg)

## 專案簡介 (Project Overview)

Gemma AI Research Assistant 是一個部署於 Google Cloud Platform (GCP) 的自動化研究助理。它能根據使用者提出的要求，在網際網路上收集資料、進行深度分析與彙整，並自動生成結構化的研究報告，存放在 Google Drive 指定的資料夾中。

本專案的核心推理引擎採用 **Gemma 4 26B**，確保在資料處理與邏輯分析上具有卓越的表現。

## 領域語言 (Ubiquitous Language)

為了確保開發與需求定義的一致性，本專案採用以下核心語彙：

| 術語 (Term) | 定義 (Definition) |
| :--- | :--- |
| **Research Task (研究任務)** | 使用者發起的單一研究指令，包含關鍵字、目標資料範圍與產出格式。 |
| **Information Fragment (資訊碎片)** | 從網路抓取的原始、未經處理的原始資料，作為後續彙整的素材。 |
| **Synthesis Engine (綜合引擎)** | 負責使用 Gemma 4 26B 進行邏輯推理、摘要與報告整合的核心模組。 |
| **Research Artifact (研究產出物)** | 最終生成的 Google Doc 或 Sheet 檔案。 |
| **Discovery Provider (探索供應者)** | 負責執行網路搜尋與網頁內容爬取的服務介面。 |
| **Delivery Provider (交付供應者)** | 負責與 Google Drive/Docs/Sheets API 互動的介面。 |

## 模組說明 (Module Description)

本專案採用 **Deep Modules (深層模組)** 設計，每個模組對外隱藏實現細節，僅暴露簡潔的介面：

*   **`src/core` (Orchestration)**: 管理研究任務的生命週期，負責各模組間的流程編排。
*   **`src/intelligence` (Synthesis)**: 封裝 Gemma 4 26B 的推論邏輯，處理長文本摘要與內容生成。
*   **`src/discovery` (Search & Scraping)**: 負責執行搜尋與資料收集工作。
*   **`src/delivery` (Persistence)**: 處理 Google Drive 與 Docs/Sheets 的寫入與格式化。
*   **`src/shared`**: 定義跨模組使用的資料型別與通用語彙。

## 技術棧 (Tech Stack)

*   **Runtime**: Python 3.11+ / Docker
*   **Deployment**: Google Cloud Run (Compute), Cloud Tasks (Queue), Firestore (Metadata)
*   **AI Engine**: Gemma 4 26B
*   **APIs**: Google Drive API, Google Docs API, Google Sheets API
