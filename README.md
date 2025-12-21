# 📈 StockSignal Intelligence v2.5

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-0066cc?logo=python)
![Gemini AI](https://img.shields.io/badge/AI-Gemini%202.0-8E75B2?logo=google)
![GoAPI](https://img.shields.io/badge/Market%20Data-GoAPI-FF5722?logo=api)
![License](https://img.shields.io/badge/License-MIT-green)

**The Ultimate AI-Powered Institutional Trading Assistant for IDX.**

StockSignal Intelligence v2.5 is a major leap forward, unifying **Technical Analysis**, **Forensic Bandarmology** (Smart Money Flow), and **Real-Time IDX News** into a single, high-speed dashboard. It acts as your personal hedge fund analyst, delivering "Buy/Hold/Sell" insights directly to your desktop and WhatsApp.

---

## 🚀 What's New in v2.5?

### 🧠 Unified Stock Intelligence Engine
*   **One Report, Total Clarity**: Merged separate Technical and Bandarmology reports into a single comprehensive "Stock Intelligence" output.
*   **Forensic AI**: New detection algorithms for "Ping-Pong" transactions, "Markdown Accumulation", and "Power Buyer" identification.
*   **Combined Charting**: Visualizes Price Action overlayed with a **Broker Flow Panel** (Green/Red Bars) for instant accumulation spotting.

### 📰 Real-Time IDX News (GoAPI)
*   **Direct Exchange Data**: Switched news source to **GoAPI IDX News** for 100% relevant, local market updates (no more generic global news noise).
*   **Smart Fallback**: Automatically switches to Google Search (Serper) if the primary feed is silent.

### ⚡ Performance Supercharge
*   **Parallel Processing**: Data fetching (Tech, Broker, News, Valuation) runs concurrently, reducing analysis time by **~40%**.
*   **Instant Launch**: Startup sequence optimized to **<1 second** by caching dependency checks.
*   **Lazy Loading**: Heavy libraries load only when needed, keeping the UI responsive.

---

## 📸 Dashboard Showcase

| **Market Analysis** | **Stock Intelligence** | **WhatsApp Alert** |
|:---:|:---:|:---:|
| ![Market Dashboard](https://via.placeholder.com/250x150?text=Price+vs+Broker+Flow) | ![Intelligence Report](https://via.placeholder.com/250x150?text=Forensic+Insight) | ![WhatsApp Alert](https://via.placeholder.com/250x150?text=Detailed+Alert) |

---

## ✨ Key Features

*   **🖥️ Professional UI**: Dark-mode dashboard with "Cyberpunk Emerald" accents, Sidebar navigation, and History/Favorites management.
*   **🐋 Bandarmology V2**:
    *   **Cumulative Distribution**: Tracks Top 3 Sellers over 20 days.
    *   **Net Foreign Flow**: Real-time foreign fund tracking.
    *   **PBV Corrector**: Auto-fixes currency mismatches (e.g., USD financials vs IDR price) for accurate valuations.
*   **🤖 Gemini 2.0 Brain**:
    *   **Risk Manager**: Generates concrete Trading Plans (Buy Area, Stop Loss, Target).
    *   **Sentiment Engine**: Analyzes news tone to gauge market psychology.
*   **📈 Portfolio Manager**: Real-time P/L tracking with live price updates.
*   **📱 Smart WhatsApp Integration**: Top-tier connectivity using `whatsapp-web.js` node service for reliable broadcasting.

---

## 📂 Project Structure

```plaintext
StockSignal-Intelligence/
├── ui/                     # Modular GUI System (Sidebar, Market, Portfolio)
├── stock-intelligence/     # Core Analytic Engine
│   ├── quant_engine.py     # Bandarmology & Broker Summary Logic
│   ├── technical_analysis.py # Indicators & Valuation Validator
│   ├── catalyst_agent.py   # AI Prompts (Forensic & Technical)
│   ├── news_fetcher.py     # Hybrid News (GoAPI + Serper)
│   └── goapi_client.py     # Direct IDX Data Client
├── whatsapp-service/       # Node.js Gateway
├── desktop_app.py          # App Launcher
└── start_app.bat           # 1-Click Fast Launcher
```

---

## 🛠️ Prerequisites

*   **Python 3.10+**: [Download](https://www.python.org/downloads/) ("Add to PATH" required).
*   **Node.js (LTS)**: [Download](https://nodejs.org/) (For WhatsApp Gateway).

---

## 🚀 Installation & Setup

### 1-Click Launch (Recommended)
Simply run **`start_app.bat`**.
*   First run: Installs all dependencies (Python + Node).
*   Next runs: Launches instantly.

### Manual Setup
```bash
# Python Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# WhatsApp Service Setup
cd whatsapp-service
npm install
cd ..

# Run
python desktop_app.py
```

---

## ⚙️ Configuration

Configure keys in the **Settings Tab** or `.env`:

```ini
GOOGLE_API_KEY=your_gemini_key       # Intelligence Brain
GOAPI_API_KEY=your_goapi_key         # Broker Summary & News
SERPER_API_KEY=your_serper_key       # News Fallback
TARGET_PHONE=6281234567890@c.us      # Default Alert Receiver
```

---

## ⚠️ Disclaimer

> **DYOR (Do Your Own Research)**
> This tool provides data-driven insights but does not guarantee profit. Trading stocks involves risk. The developed Confidence Score is experimental.

---

## 📄 License
Distributed under the **MIT License**.
