# 📈 StockSignal Intelligence

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-0066cc?logo=python)
![Gemini AI](https://img.shields.io/badge/AI-Gemini%202.0-8E75B2?logo=google)
![Node.js](https://img.shields.io/badge/WhatsApp-Node.js%20Service-339933?logo=nodedotjs)
![License](https://img.shields.io/badge/License-MIT-green)

**An AI-powered institutional trading assistant for the Indonesian Stock Exchange (IDX).**

StockSignal Intelligence fuses **Technical Analysis**, **Bandarmology (Smart Money Flow)**, and **AI-driven Sentiment Analysis** into a single, Bloomberg-terminal style dashboard. It delivers actionable "Buy/Hold/Sell" insights directly to your WhatsApp with one click.

---

## 📸 Dashboard Showcase

| **Market Analysis** | **Portfolio Tracker** | **WhatsApp Alert** |
|:---:|:---:|:---:|
| ![Market Dashboard](https://via.placeholder.com/250x150?text=Market+Dashboard) | ![Portfolio Manager](https://via.placeholder.com/250x150?text=Portfolio+View) | ![WhatsApp Alert](https://via.placeholder.com/250x150?text=WhatsApp+Alert) |

---

## ✨ Key Features (v2.1 Update)

*   **🖥️ Bloomberg-Style Interface**: A completely redesigned dark-mode UI with "Cyberpunk Emerald" accents, dedicated terminals, and professional charting.
*   **🐋 Advanced Bandarmology**: Integration with **GoAPI** to analyze real Broker Summary (Top Buyers/Sellers) and Foreign Flow accumulation.
*   **🤖 Gemini 2.0 Brain**: Synthesizes chart patterns, volume anomalies, and news sentiment into human-readable trading plans.
*   **📈 Portfolio Manager**: Real-time P/L tracking with live price updates via YFinance. Calculate Equity, Gain/Loss, and % Return instantly.
*   **📱 Smart WhatsApp Integration**:
    *   One-click broadcast of charts + reports.
    *   Built-in **Group ID Scanner** to easily target WhatsApp Groups.
*   **⚙️ Zero-Code Configuration**: Manage your API keys and target numbers directly from the new **Settings GUI**.

---

## 📂 Project Structure

The project has been refactored for modularity and scalability:

```plaintext
StockSignal-Intelligence/
├── ui/                     # Modular UI Components
│   ├── app.py              # Main Application Container
│   ├── sidebar.py          # Navigation & Favorites
│   ├── market_view.py      # Technical Analysis Dashboard
│   ├── portfolio_view.py   # Portfolio Management
│   └── settings_view.py    # GUI Config Manager
├── stock-intelligence/     # Core Logic Engine
│   ├── quant_engine.py     # Bandarmology Algorithms
│   ├── technical_analysis.py # TA Indicators (RSI, MACD, OBV)
│   └── app_controller.py   # Bridge between UI and Logic
├── whatsapp-service/       # Node.js Gateway
│   └── index.js            # whatsapp-web.js Service
├── desktop_app.py          # Application Launcher
└── start_app.bat           # Auto-Setup Script
```

---

## 🛠️ Prerequisites

*   **Python 3.10+**: [Download](https://www.python.org/downloads/) (Check **"Add to PATH"** during install).
*   **Node.js (LTS)**: [Download](https://nodejs.org/) (Required for WhatsApp gateway).
*   **Git**: [Download](https://git-scm.com/).

---

## 🚀 Installation & Setup

### Option 1: The "One-Click" Method (Recommended)
Simply double-click **`start_app.bat`**. This script will automatically:
1.  Check for Python & Node.js.
2.  Create a virtual environment (`venv`).
3.  Install all Python dependencies.
4.  Install Node.js modules for WhatsApp.
5.  Launch the application.

### Option 2: Manual Setup
```bash
# 1. Create & Activate Venv
python -m venv venv
venv\Scripts\activate

# 2. Install Python Deps
pip install -r requirements.txt

# 3. Install Node Deps
cd whatsapp-service
npm install
cd ..

# 4. Run App
python desktop_app.py
```

---

## ⚙️ Configuration

You can now configure the app directly via the **GUI Settings Tab**, or manually edit the `.env` file:

```ini
GOOGLE_API_KEY=your_gemini_api_key      # Required: AI Analysis
SERPER_API_KEY=your_serper_api_key      # Required: Real-time News
GOAPI_API_KEY=your_goapi_key            # Optional: Real Bandarmology Data
TARGET_PHONE=6281234567890@c.us         # Default WhatsApp Recipient
```

*   **Tip**: Use the **Info Tab -> Scan Groups** feature in the app to find your Group ID (ends in `@g.us`).

---

## ⚠️ Disclaimer

> **DYOR (Do Your Own Research)**
> This software is for educational and informational purposes only. The "Confidence Score" and AI recommendations are generated based on historical data and algorithms, which may not predict future results. The developer is not responsible for any financial losses incurred from using this tool.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
