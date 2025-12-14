import argparse
import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from technical_analysis import analyze_technical
from catalyst_agent import get_ai_analysis
from news_fetcher import fetch_stock_news
from chart_generator import generate_chart

# Configuration
WHATSAPP_SERVICE_URL = "http://localhost:3000/send"
# Default phone number to send to (can be env var or arg)
DEFAULT_PHONE = os.getenv("TARGET_PHONE", "") 

def format_message(ticker, ta_data, ai_analysis, news_summary=""):
    """
    Formats the final message (Technical & Volume Focused).
    """
    trend_emoji = "📈" if "Bullish" in ta_data['trend'] else "📉"
    vol_emoji = "🔥" if ta_data['vol_ratio'] > 1.5 else "💤"
    
    # Clean up news summary for better display if it exists
    news_section = ""
    if news_summary:
        news_section = f"\n🌍 *SENTIMEN BERITA (Update):*\n{news_summary}\n"
    
    message = f"""🚨 *STOCK INTELLIGENCE: ${ticker}*

📊 *DATA TEKNIKAL & VOLUME FLOW:*
• *Tren:* {ta_data['trend']} {trend_emoji}
• *Candle:* {ta_data.get('candle_pattern', '-')}
• *MACD:* {ta_data['macd_status']}
• *Volume Flow:* {ta_data['bandar_status']}
• *Indikasi:* {ta_data['bandar_action']}
• *MFI (Money Flow):* {ta_data.get('mfi', 50):.2f}
• *Holder Utama:* {ta_data.get('major_holders', 'N/A')}
• *Harga:* {ta_data['price']:.0f}
• *Volume:* {ta_data['vol_status']} {vol_emoji}
• *RSI:* {ta_data['rsi']:.2f} | *ADX:* {ta_data.get('adx', 0):.2f}
{news_section}
🤖 *ANALISA AI (Smart Money & News):*
{ai_analysis}

🎯 *RENCANA TRADING:*
• *Area Entry:* {ta_data['price']:.0f}
• *Target (TP):* {ta_data['target']:.0f}
• *Stop Loss (SL):* {ta_data['stop_loss']:.0f}

_Dibuat oleh StockSignal Bot_"""
    return message

def broadcast_message(phone, message, media_path=None):
    """
    Sends the message to the Node.js WhatsApp service.
    Supports optional media (image) attachment.
    """
    if not phone:
        print("No phone number provided. Skipping WhatsApp broadcast.")
        print("--- Generated Message ---")
        print(message)
        return

    payload = {
        "number": phone,
        "message": message
    }
    
    if media_path:
        payload["image_path"] = media_path
    
    try:
        response = requests.post(WHATSAPP_SERVICE_URL, json=payload)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error connecting to WhatsApp Service: {str(e)}")
        print("Ensure the Node.js service is running on port 3000.")

def main():
    parser = argparse.ArgumentParser(description="StockSignal Deep-Dive Bot")
    parser.add_argument("ticker", help="Stock Ticker (e.g., AAPL, BBCA.JK)")
    parser.add_argument("--phone", help="Target WhatsApp Number (e.g., 6281234567890)", default=DEFAULT_PHONE)
    args = parser.parse_args()

    ticker = args.ticker.upper()
    print(f"Starting analysis for {ticker}...")

    # 1. Technical Analysis
    try:
        print("Running Technical Analysis...")
        ta_data = analyze_technical(ticker)
    except Exception as e:
        print(f"Technical Analysis Failed: {e}")
        sys.exit(1)

    # 2. News Search (Catalyst)
    print("Running News Search (Serper)...")
    news_summary = fetch_stock_news(ticker)
    
    # 3. Chart Generation (Proof)
    print("Generating Chart...")
    chart_path = generate_chart(ticker, ta_data['df_daily'])

    # 4. AI Analysis
    print("Running AI Technical Analysis (Gemini)...")
    ai_result = get_ai_analysis(ta_data['ticker'], ta_data, news_summary)
    
    # Handle AI Result (Dict or String)
    if isinstance(ai_result, dict):
        ai_analysis = ai_result.get('analysis', "Error parsing AI analysis.")
        # sentiment_score = ai_result.get('sentiment_score', 50) # Use if needed in future features
    else:
        ai_analysis = str(ai_result)

    # 5. Format Message
    final_message = format_message(ta_data['ticker'], ta_data, ai_analysis, news_summary)

    # 6. Broadcast
    broadcast_message(args.phone, final_message, chart_path)

if __name__ == "__main__":
    main()
