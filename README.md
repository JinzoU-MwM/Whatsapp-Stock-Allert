# 📈 WhatsApp Stock Intelligence Bot (WSIB)

**AI-Powered Stock Analysis & Bandarmology Forensic Tool**

WSIB is an advanced stock analysis platform that integrates **Technical Analysis**, **Fundamental Valuation**, and **Bandarmology Forensic** into a single, comprehensive report delivered directly via **WhatsApp**. It leverages **Google Gemini 1.5 Pro/Flash** to synthesize complex market data into actionable trading insights.

## 🚀 Key Features

### 🧠 AI Stock Intelligence
*   **Unified Analysis**: Combines Technical (Price Action, Indicators), Fundamental (Valuation, Growth), and Bandarmology (Flow Analysis) into one report.
*   **Gemini 1.5 Powered**: Uses state-of-the-art AI to interpret data, not just display it.
*   **Smart Agents**:
    *   **Technical Agent**: Analyzes Trend, Momentum, and Divergence.
    *   **Forensic Agent**: Detects Accumulation/Distribution, "Inventory Dumping", and Market Maker movements.
    *   **Fundamental Agent**: Evaluates Valuation (PER/PBV), Profitability (ROE), and Financial Health (DER).
    *   **CIO Agent**: Synthesizes all inputs into a final **Verdict** (BUY/SELL/WAIT) with a Confidence Score.

### 🕵️ Bandarmology Forensic
*   **Real-Time Flow**: Analyzes daily Broker Summary (Top Buyers/Sellers) to detect Big Player movement.
*   **Historical Analysis**: Tracks **20-day Cumulative Net Flow** to identify massive accumulation or hidden distribution.
*   **Broker Flow Chart**: Visualizes Net Volume flow (Green = Accumulation, Red = Distribution) alongside Price action.

### � Data & Accuracy
*   **GoAPI Integration (Premium)**:
    *   **Real-Time Prices**: Accurate market data.
    *   **Official Broker Summary**: Detailed broker transaction data.
    *   **Accurate Valuation**: Uses official IDX Profile data for PER, PBV, and EPS (solving common Yahoo Finance errors for stocks like BUMI).
*   **News Intelligence**:
    *   Fetches latest news via **GoAPI** (filtered for current year) or **Google Search (Serper)**.
    *   Ensures you never see outdated headlines.

### 📱 WhatsApp Integration
*   **Professional Reports**: Beautifully formatted reports using professional styling (bullets, separators).
*   **Actionable Plans**: Clear "Action Plan" with Buy Areas, Stop Loss, and Target Prices.
*   **Chart Delivery**: Sends analyzed charts directly to your chat.

## �️ Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/JinzoU-MwM/Whatsapp-Stock-Allert.git
    cd Whatsapp-Stock-Allert
    ```

2.  **Install Dependencies**:
    The system auto-installs on first run, or manually:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    Create a `.env` file in the root directory:
    ```env
    GOOGLE_API_KEY=your_gemini_key
    SERPER_API_KEY=your_serper_key
    GOAPI_API_KEY=your_goapi_key
    TARGET_PHONE=628...
    AI_MODEL=gemini-1.5-flash
    ```

4.  **WhatsApp Service**:
    Ideally runs with a companion Node.js service (included in `whatsapp-service/`) utilizing `whatsapp-web.js`.

## �️ Usage

### GUI Mode (Recommended)
Double-click `start_app.bat`.
1.  **Scan QR Code**: Connect your WhatsApp.
2.  **Dashboard**:
    *   **Market**: Quick Technical Analysis.
    *   **Bandarology**: Deep-dive Broker Flow analysis.
    *   **Portfolio**: Track your holdings with Real-Time P/L.

### Command Line
```bash
python stock-intelligence/main.py BBCA
```

## 📝 Recent Updates
*   **BUMI Fix**: Fixed "Merugi" status by switching Valuation data to GoAPI.
*   **News Filter**: Added strict Year Filter (2025) to prevent outdated news.
*   **Smart Formatting**: Improved bullet points and nesting for readable Action Plans.
*   **BSML Fix**: Resolved missing Bandarmology data issues for stocks with limited history.

---
**Disclaimer**: This tool provides analysis based on data and AI interpretation. It is not financial advice. Always do your own research (DYOR).
