# 📈 WhatsApp Stock Intelligence Bot (WSIB) v2.5

**AI-Powered Stock Analysis | Top-Down Bandarmology | Multi-Strategy**

WSIB is an advanced **Agentic AI** platform that acts as your personal **Chief Investment Officer (CIO)**. It integrates **Technical Analysis**, **Fundamental Valuation**, and **Forensic Bandarmology** into a single, comprehensive report delivered via **WhatsApp**. It leverages **Google Gemini 2.0 Flash/Pro** to synthesize complex market data into actionable trading plans.

## 🚀 Key Features

### 🧠 Adaptive AI Intelligence
*   **Multi-Strategy Support**:
    *   **SCALPING**: AI acts as an Aggressive Day Trader. Focus on Volume Spikes, Momentum, and Intraday Flow. Ignores Fundamentals.
    *   **SWING (Default)**: Balanced approach. Combines Trend Following with Bandarmology Accumulation.
    *   **INVESTING**: AI acts as a Value Investor. Focus on Undervalued Gems (PBV/PER) and Long-Term Accumulation ("The Map").
*   **Unified Verdict**: A "CIO Agent" synthesizes Technical, Fundamental, and Bandar reports into a final decision with a precise **Confidence Score**.

### 🕵️ Advanced Bandarmology (Top-Down Forensic)
*   **"The Map" (Periodic Analysis)**: Analyzes the Big Picture (e.g., last 20 days). Detects if the Big Player (Bandar) is holding goods or distributing.
*   **"The Trigger" (Daily Analysis)**: Analyzes today's flow. Is it a real buy or a trap?
*   **Smart Logic**:
    *   **Markdown Accumulation**: Detects when average price of Bandar is above market price (Potential Reversal).
    *   **Bull Trap**: Detects price rise but accompanied by massive Distribution.

### 🛡️ Robust Technicals & Trading Plans
*   **Always-On Plan**: AI generates specific **Buy Areas**, **Stop Loss (ATR Based)**, and **Profit Targets** regardless of market condition (even in Bearish trends for "Watchlist" purposes).
*   **Auto-Correction**: Self-healing data pipeline that prioritizes local calculation for Critical Indicators (RSI, Pivot Points) to prevent API lag.
*   **Data Accuracy**:
    *   **GoAPI Integration (Premium)**: Official IDX Broker Summary & Real-Time Prices.
    *   **Yahoo Finance Fallback**: Robust fallback for global data.

### 📱 WhatsApp Integration
*   **Professional Reports**: Beautifully formatted with professional aesthetics (bullets, bolding, separators).
*   **Chart Delivery**: Sends analyzed technical charts directly to your chat.
*   **Broadcast Capable**: Send analysis to groups or specific numbers.

## 🛠️ Installation

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
    GOAPI_API_KEY=your_goapi_key (Optional but Recommended for Indo Stocks)
    TARGET_PHONE=628...
    AI_MODEL=gemini-2.0-flash-exp
    ```

4.  **Start Application**:
    Double-click `start_app.bat` (Windows).

## 🖥️ Usage

### GUI Dashboard
1.  **Select Strategy**: Choose between `SCALPING`, `SWING`, or `INVESTING` from the dropdown.
2.  **Enter Ticker**: Type `BBRI`, `BMRI`, etc.
3.  **Run Analysis**: The AI agents will perform parallel research and generate a comprehensive report.
4.  **Send**: Click "Send WhatsApp" to forward the report to your phone.

### Command Line
```bash
python stock-intelligence/main.py BBCA
```

## 📝 Recent Version 2.5 Updates
*   **Feature**: **Selectable Strategies** (Scalping vs Swing vs Invest) in UI.
*   **Logic**: **Top-Down Bandarmology** implemented. AI now compares "The Map" (Periodic) vs "The Trigger" (Daily).
*   **Fix**: Resolved **RSI Anomaly** by strictly using local calculation over API pre-computed values.
*   **UX**: Added **Strategy Dropdown** in the Market View.

---
**Disclaimer**: This tool provides analysis based on data and AI interpretation. It is not financial advice. Always do your own research (DYOR).
