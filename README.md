# StockSignal Intelligence (Bloomberg Edition)

An AI-powered stock analysis tool that combines Technical Analysis, Bandarmology (Volume Flow), and Real-time News Sentiment to generate actionable trading insights. The results are broadcasted directly to WhatsApp.

![StockSignal Dashboard](https://via.placeholder.com/800x400?text=StockSignal+Dashboard)

## ✨ New Features (Dec 2025 Update)

*   **📈 Portfolio Management**: Track your stock portfolio with Real-Time P/L calculation (Equity, %, Gain/Loss).
*   **🖥️ Bloomberg-Style UI**: A completely redesigned, dark-themed professional dashboard with "Cyberpunk/Emerald" aesthetics.
*   **📊 Advanced Technicals**: Added MFI, OBV, ADX, ATR, and Candlestick Pattern detection.
*   **🐋 Bandarmology**: Integration with **GoAPI** for real Broker Summary and Foreign Flow analysis.
*   **🤖 One-Click Setup**: Enhanced `start_app.bat` that auto-installs Python/Node.js dependencies.
*   **📱 WhatsApp Group Scanner**: Dedicated tool to easily find and copy Group IDs for broadcasting.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your computer:

1.  **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
    *   *Important*: During installation, check the box **"Add Python to PATH"**.
2.  **Node.js & npm** (Required for WhatsApp Service): [Download Node.js](https://nodejs.org/)
    *   Download the "LTS" version.
3.  **Git**: [Download Git](https://git-scm.com/downloads)

---

## 📦 Installation Guide

Follow these steps precisely to set up the project on a new computer.

### 1. Clone the Repository
Open your terminal (Command Prompt or PowerShell) and run:
```bash
git clone https://github.com/JinzoU-MwM/Whatsapp-Stock-Allert.git
cd Whatsapp-Stock-Allert
```

### 2. Auto-Setup (Recommended)
Simply double-click the **`start_app.bat`** file.
*   It will check for Python & Node.js.
*   It will create the virtual environment (`venv`).
*   It will install all Python `requirements.txt`.
*   It will install Node.js modules for the WhatsApp service.
*   It will launch the dashboard.

### 3. Manual Setup (Alternative)
If the batch file fails, run these commands:
```bash
# Create venv
python -m venv venv
venv\Scripts\activate

# Install Python deps
pip install -r requirements.txt

# Install Node deps
cd whatsapp-service
npm install
cd ..
```

### 4. Configure Environment Variables
1.  Copy the example configuration file:
    ```bash
    copy .env.example .env
    ```
2.  Open `.env` with a text editor and fill in your keys:
    ```ini
    GOOGLE_API_KEY=your_gemini_api_key
    SERPER_API_KEY=your_serper_api_key
    GOAPI_API_KEY=your_goapi_key_here (Optional: For Real Bandarmology)
    TARGET_PHONE=6281234567890@c.us
    ```

---

## 🚀 How to Use

### 1. Market Data Analysis
*   Enter a ticker (e.g., `BBCA`, `TLKM`) in the top bar.
*   Select Timeframe (Daily/Weekly).
*   Click **RUN ANALYSIS ⚡**.
*   View the Confidence Score, AI Report, and Chart in the "Report Preview" tab.
*   Click **Send WhatsApp** to broadcast the result.

### 2. Portfolio Management
*   Switch to the **PORTFOLIO** tab in the sidebar.
*   Add your positions (Ticker, Avg Price, Lots).
*   Click **REFRESH PRICES ⚡** to see your current Market Value and P/L% based on real-time data.

### 3. WhatsApp Integration
*   **First Run**: The app will show a QR Code. Scan it with your phone (Linked Devices).
*   **Groups**: Go to the **INFO** tab -> Click **Scan WhatsApp Group IDs**. Copy the ID (ends in `@g.us`) to your `.env` file as `TARGET_PHONE`.

---

## 📜 Changelog (Latest)

*   **Refactor**: Split monolithic `desktop_app.py` into modular UI components (`ui/sidebar.py`, `ui/market_view.py`, etc.).
*   **UI Polish**: Fixed sidebar layout, logout button visibility, and header alignment.
*   **Feature**: Added Portfolio Management with SQLite database and YFinance pricing.
*   **Feature**: Added "System Logs" and "Info" tabs with dedicated output terminals.
*   **Fix**: Resolved GoAPI date logic for EOD broker summary data.
*   **Fix**: Robust error handling for application startup.

---

## ❓ Troubleshooting

**Q: The app opens but shows an error popup.**
*   Read the traceback in the popup. It usually means a missing library or API key.

**Q: WhatsApp Logout button is hidden.**
*   The sidebar layout has been optimized. Try resizing the window taller, although the latest update (v2.1) compacted the lists to fix this.

## 📄 License
MIT License
