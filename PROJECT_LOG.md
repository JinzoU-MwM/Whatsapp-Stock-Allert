# Project Intelligence Log & Context

> **PURPOSE:** This document serves as a persistent memory and context buffer for AI agents working on this project. It tracks architecture, recent updates, debugging history, and future roadmaps. **DO NOT COMMIT THIS FILE TO GIT.**

## 1. Project Overview
**Name:** StockSignal Intelligence (Whatsapp-Stock-Allert)
**Goal:** Institutional-grade stock analysis bot for IDX (Indonesia Stock Exchange).
**Core Functions:**
1.  **Technical Analysis:** Uses `pandas_ta` + `yfinance` + `GoAPI` (Hybrid).
2.  **Bandarmology (Smart Money):** Uses `GoAPI` for real Broker Summary and Foreign Flow.
3.  **Valuation:** Uses `yfinance` fundamentals (PER, PBV, ROE).
4.  **AI Insight:** Uses `Google Gemini 2.0` to synthesize data into trading plans.
5.  **Delivery:** Broadcasts alerts via WhatsApp (Node.js service).

## 2. Architecture Stack
*   **Language:** Python 3.10+ (Logic), Node.js (WhatsApp Gateway).
*   **GUI:** CustomTkinter (`ui/`).
*   **Database:** SQLite (`stock_intelligence.db`) for history, portfolio, and cache.
*   **APIs:**
    *   `Google Gemini`: AI Analysis.
    *   `Serper.dev`: Real-time News.
    *   `GoAPI.io`: Bandarmology (Broker Sum) & Official Indicators.
    *   `YFinance`: Price History & Valuation.

## 3. Key Modules
*   `stock-intelligence/app_controller.py`: Main orchestrator. Handles hot-reload of keys.
*   `stock-intelligence/technical_analysis.py`:
    *   **Hybrid Data:** Merges YFinance history with GoAPI Real-time price.
    *   **Hybrid Indicators:** Overwrites calculated RSI/EMA with Official GoAPI values if available.
    *   **Valuation:** Fetches fundamental data using `.JK` suffix logic.
*   `stock-intelligence/quant_engine.py`:
    *   Analyzes Broker Summary (Accumulation/Distribution).
    *   Calculates Top 3 Buyer Average Price.
    *   **Fix:** Ensures summary is returned even if status is "Neutral".
*   `stock-intelligence/catalyst_agent.py`: Interfaces with Gemini. Prompt includes Technicals, Bandarmology, Fundamentals, and News.
*   `ui/settings_view.py`: Config management with Hot-Reload support.

## 4. Recent Changelog (As of Dec 16, 2025)

### ✅ Feature: Fundamental Valuation
*   **Added:** `technical_analysis.py` now fetches PER, PBV, ROE, Market Cap.
*   **Logic:** Uses `yfinance.Ticker(symbol).info`. Added fallback to `symbol.JK` to ensure data retrieval for IDX stocks.
*   **UI:** Added "💰 FUNDAMENTAL & VALUASI" section to the WhatsApp message.

### ✅ Feature: GoAPI Integration Improvements
*   **Indicators:** Added `get_indicators` endpoint to `goapi_client.py`.
*   **Hybrid TA:** `analyze_technical` now prioritizes GoAPI indicators (RSI, EMA) over local calc for accuracy.
*   **Broker Summary:** Fixed bug where "Neutral" bandar status resulted in empty details. Now always returns summary.
*   **Avg Price:** Added `avg_bandar_price` (Average price of Top 3 Buyers) to analysis.

### ✅ Feature: Settings Hot-Reload & AI Models
*   **Hot-Reload:** Updating API Keys or AI Model in Settings now re-initializes clients without app restart.
*   **Models:** Updated list to support `gemini-2.0-flash-exp`, `gemini-2.5`, and `deep-research-pro-preview`.

### ✅ Feature: Advanced Trading Logic (Pivot Points)
*   **Pivot Points:** Added Classic Pivot Point calculation (Pivot, R1, S1, R2, S2) in `technical_analysis.py`.
*   **Trading Plan:** `main.py` now generates entry/target/SL levels dynamically based on these pivots (e.g., Entry: S1-Pivot, Target: R1-R2).
*   **Refactor:** Extracted `get_valuation_data` into a standalone function for better modularity.

### 🐛 Bug Fixes
*   **Unicode Crash:** Fixed Windows console crash caused by printing unsupported emojis (🤖) in logs. Added safe ASCII encoding for debug prints.
*   **Empty Summary:** Fixed logic in `quant_engine.py` / `main.py` that suppressed broker summary text for neutral flows.

## 5. Known Constraints & Context
*   **YFinance MultiIndex:** Recent `yfinance` versions return MultiIndex columns. We flatten them (`df.columns = df.columns.get_level_values(0)`) in `technical_analysis.py`.
*   **GoAPI Limits:** Free tier might have delayed broker summary. Code handles empty responses gracefully.
*   **Windows Console:** Command prompt doesn't support all emojis. Use `safe_print` or `encode/decode` for debug logs.

## 6. Future Roadmap (Todo)
*   [ ] **Portfolio:** Advanced P/L visualizations.
*   [ ] **Alerts:** Automated price alerts (Cron job style).
*   [ ] **Backtesting:** Simple backtest engine for the "Verdict" logic.

## 7. How to Resume Work
1.  **Check `PROJECT_LOG.md`** (This file) for context.
2.  **Run Tests:** Use `verify_pipeline.py` (if exists) or create a small script to test `analyze_technical('BBCA')`.
3.  **Logs:** Check `whatsapp-service/service_debug.log` for WhatsApp issues.
