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

### 2. Set up Python Environment
Create a virtual environment to avoid conflicts:
```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
*If you are on Mac/Linux, use `source venv/bin/activate`.*

### 3. Set up WhatsApp Service (Node.js)
Install the dependencies for the WhatsApp gateway:
```bash
cd whatsapp-service
npm install
cd ..
```

### 4. Configure Environment Variables
1.  Copy the example configuration file:
    ```bash
    copy .env.example .env
    ```
    *(Or manually create a file named `.env`)*

2.  Open `.env` with a text editor (Notepad, VS Code) and fill in your keys:
    ```ini
    GOOGLE_API_KEY=your_gemini_api_key_here
    SERPER_API_KEY=your_serper_api_key_here
    TARGET_PHONE=6281234567890@c.us
    ```
    *   **GOOGLE_API_KEY**: Get it from [Google AI Studio](https://aistudio.google.com/).
    *   **SERPER_API_KEY**: Get it from [Serper.dev](https://serper.dev/).
    *   **TARGET_PHONE**: Your WhatsApp number (start with country code, e.g., 62 for Indonesia). 
        *   For personal chat: `6281234567890@c.us`
        *   For groups: Use the "Cari ID Grup WhatsApp" feature in the app to find the ID (ends in `@g.us`).

---

## 🚀 How to Run

### Method 1: The Easy Way (Windows)
Double-click the **`start_app.bat`** file. 
*   This script automatically activates the virtual environment and launches the dashboard.

### Method 2: Manual Run
1.  Open terminal in the project folder.
2.  Activate Python: `venv\Scripts\activate`
3.  Run the app:
    ```bash
    python desktop_app.py
    ```

---

## 📱 WhatsApp Authentication (First Time Only)

1.  When you run the app for the first time, a **console window** (black screen) will appear for the `whatsapp-service`.
2.  It will generate a **QR Code**.
3.  Open WhatsApp on your phone -> **Linked Devices** -> **Link a Device**.
4.  Scan the QR Code.
5.  Once connected, you can close and restart the app. Future runs will hide this console window automatically.

---

## ❓ Troubleshooting

**Q: The app opens but closes immediately.**
*   Check if you installed dependencies: `pip install -r requirements.txt`.
*   Check if you have `Node.js` installed.

**Q: "ModuleNotFoundError"**
*   Make sure you activated the virtual environment (`venv\Scripts\activate`) before running python commands.

**Q: WhatsApp service error / Chromium error**
*   The `whatsapp-web.js` library needs a browser. It usually downloads Chromium automatically. If it fails, try running `npm install` inside the `whatsapp-service` folder again.

**Q: News fetch failed**
*   Check your `SERPER_API_KEY` in the `.env` file.

**Q: AI Analysis error**
*   Check your `GOOGLE_API_KEY` in the `.env` file.

## 📄 License
MIT License
