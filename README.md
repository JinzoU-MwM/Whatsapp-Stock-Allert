# StockSignal Intelligence (Antigravity Edition) 🚀

An AI-powered stock analysis tool that combines Technical Analysis, Bandarmology (Volume Flow), and Real-time News Sentiment to generate actionable trading insights. The results are broadcasted directly to WhatsApp.

![StockSignal Dashboard](https://via.placeholder.com/800x400?text=StockSignal+Dashboard)

## ✨ Features

*   **Deep Dive Analysis**: Analyzes stock technicals (Daily & Weekly trends), RSI, and Volume Flow.
*   **Smart Money Flow (Bandarmology Proxy)**: Detects potential Big Money accumulation or distribution based on Price-Volume Action.
*   **Real-Time News**: Fetches the latest specific news for the stock from Indonesian sources.
*   **AI Reasoning (Gemini 2.0)**: Synthesizes data + news to provide a human-like summary and recommendation (Buy/Hold/Sell).
*   **WhatsApp Integration**: Sends the full report + Chart Image to your WhatsApp.
*   **Chart Generation**: Auto-generates Candlestick charts with EMA 20/50 and Volume.

## 🛠️ Prerequisites

*   **Python 3.10+**
*   **Node.js & npm** (for WhatsApp Service)
*   **Google Gemini API Key** (Free)
*   **Serper.dev API Key** (for News Search)

## 📦 Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/JinzoU-MwM/Whatsapp-Stock-Allert.git
    cd Whatsapp-Stock-Allert
    ```

2.  **Set up Python Environment**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r stock-intelligence/requirements.txt
    ```

3.  **Set up Node.js Service**
    ```bash
    cd whatsapp-service
    npm install
    cd ..
    ```

4.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```ini
    GOOGLE_API_KEY=your_gemini_api_key
    SERPER_API_KEY=your_serper_api_key
    TARGET_PHONE=6281234567890@c.us
    ```
    *Note: Use the "Cari ID Grup WhatsApp" button in the app to find Group IDs (ending in @g.us).*

## 🚀 Usage

1.  **Run the Application**
    Double-click `start_app.bat` or run:
    ```bash
    start_app.bat
    ```

2.  **Authenticate WhatsApp**
    *   On the first run, a console window will appear with a QR Code.
    *   Scan it using WhatsApp (Linked Devices).
    *   Once authenticated, restart the app. The console will be hidden in future runs.

3.  **Analyze a Stock**
    *   Enter a Ticker (e.g., `BBRI`, `GOTO`, `NVDA`).
    *   Click **"Analisa Lengkap"**.
    *   Wait for the AI to "Think" (logs will appear).
    *   Review the preview and click **"Kirim ke WhatsApp"**.

## 📂 Project Structure

```
Whatsapp-Stock-Allert/
├── desktop_app.py              # Main GUI Dashboard (CustomTkinter)
├── start_app.bat               # Launcher Script
├── stock-intelligence/         # Python Core Logic
│   ├── main.py                 # Core orchestration
│   ├── technical_analysis.py   # TA & Volume Flow Logic
│   ├── catalyst_agent.py       # AI (Gemini) Handler
│   ├── news_fetcher.py         # News Scraper (Serper)
│   ├── chart_generator.py      # Charting (Mplfinance)
│   └── db_manager.py           # SQLite Caching
└── whatsapp-service/           # Node.js WhatsApp Gateway
    ├── index.js                # Express Server + whatsapp-web.js
    └── package.json
```

## ⚠️ Disclaimer

This tool is for **educational purposes only**. Stock trading involves risk. The AI generation is probabilistic and should not be taken as financial advice. Always do your own research (DYOR).

## 📄 License

MIT License
