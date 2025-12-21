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
from quant_engine import QuantAnalyzer
try:
    from goapi_client import GoApiClient
except ImportError:
    GoApiClient = None

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
    
    # Valuation Data Extraction
    val_data = ta_data.get('valuation', {})
    val_status = val_data.get('valuation_status', 'N/A')
    per_val = val_data.get('per', 0)
    pbv_val = val_data.get('pbv', 0)
    roe_val = val_data.get('roe', 0) * 100 # Convert to %
    
    # Format Valuation Section
    valuation_section = f"""💰 *FUNDAMENTAL & VALUASI:*
• *Status:* {val_status}
• *PER:* {per_val:.2f}x | *PBV:* {pbv_val:.2f}x
• *ROE:* {roe_val:.2f}%
"""

    # Clean up news summary for better display if it exists
    news_section = ""
    if news_summary:
        news_section = f"\n🌍 *SENTIMEN BERITA (Update):*\n{news_summary}\n"
    
    message = f"""🚨 *STOCK INTELLIGENCE: ${ticker}*

🎯 *VERDICT: {ta_data.get('verdict', 'N/A')}*
🔥 *Confidence Score: {ta_data.get('final_score', 0)}/100*

📊 *DATA TEKNIKAL & VOLUME FLOW:*
• *Tren:* {ta_data['trend']} {trend_emoji}
• *Candle:* {ta_data.get('candle_pattern', '-')}
• *MACD:* {ta_data['macd_status']}
• *Volume Flow:* {ta_data['bandar_status']}
• *Foreign Flow:* {ta_data.get('foreign_status', 'N/A')}
• *Indikasi:* {ta_data['bandar_action']}
• *Detail Bandar:* {ta_data.get('bandar_summary', '-')}
• *MFI (Money Flow):* {ta_data.get('mfi', 50):.2f}
• *Holder Utama:* {ta_data.get('major_holders', 'N/A')}
• *Harga:* {ta_data['price']:.0f}
• *Volume:* {ta_data['vol_status']} {vol_emoji}
• *RSI:* {ta_data['rsi']:.2f} | *ADX:* {ta_data.get('adx', 0):.2f}

{valuation_section}{news_section}
🤖 *ANALISA AI (Smart Money & News):*
{ai_analysis}

🎯 *RENCANA TRADING (Classic Pivot):*
• *Area Entry:* {ta_data.get('pivots', {}).get('s1', ta_data['price']):.0f} - {ta_data.get('pivots', {}).get('pivot', ta_data['price']):.0f}
• *Target (TP):* {ta_data.get('pivots', {}).get('r1', ta_data['target']):.0f} - {ta_data.get('pivots', {}).get('r2', ta_data['target']):.0f}
• *Stop Loss (SL):* {ta_data.get('pivots', {}).get('s2', ta_data['stop_loss']):.0f}

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
        try:
            print(message)
        except UnicodeEncodeError:
            print(message.encode('ascii', 'ignore').decode('ascii'))
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
    parser.add_argument("ticker", help="Stock Ticker (e.g., AAPL, BBCA.JK)")
    parser.add_argument("--phone", help="Target WhatsApp Number (e.g., 6281234567890)", default=DEFAULT_PHONE)
    parser.add_argument("--include-history", action="store_true", help="Include historical broker summary (slower)")
    parser.add_argument("--mode", choices=['default', 'bandar'], default='default', help="Analysis Mode")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    print(f"Starting analysis for {ticker} (Mode: {args.mode})...")
    
    # 0. Special Mode: Bandar History
    if args.mode == 'bandar':
        # Replicates logic from run_bandar_analysis in controller but for CLI
        from app_controller import StockAppController
        
        # We instantiate controller for convenience to reuse logic, or we reproduce it here.
        # Reproducing is safer to keep main.py as a script, but we can reuse if we import controller.
        # To avoid circular import issues if app_controller imports main, we'll keep logic inline or careful.
        # Actually app_controller imports main (format_message).
        
        # Let's keep it simple: Main.py is the entry point, it can invoke controller logic if refactored, 
        # or we implement "Bandar Mode" inline here using the new tools.
        
        # ... logic ...
        # For now, let's just use the controller if possible or duplicate the fetching logic for CLI tool.
        # Given potential circular deps, I will duplicate the simple fetch-analyze-chart logic here for CLI robustness.
        pass # To be implemented in next block if needed, but for now user only asked for GUI menu.
        # I'll focus on the GUI flow which calls controller.run_bandar_analysis.
        # But for CLI completeness, let's support it.
        pass


    # 0. Special Mode: Bandar History
    if args.mode == 'bandar':
        try:
            print("🚀 Running BANDAROLOGY Mode...")
            ta_data = analyze_technical(ticker)
            
            goapi_key = os.getenv("GOAPI_API_KEY")
            if not goapi_key or not GoApiClient:
                print("❌ GoAPI Key missing. Cannot run Bandar analysis.")
                return

            client = GoApiClient(goapi_key)
            quant = QuantAnalyzer(client)
            
            print("Fetching 20 Days Broker History...")
            hist_raw = client.get_broker_summary_historical(ticker, days=20)
            broker_history_df = quant.analyze_historical_broker_summary(hist_raw)
            
            summary_text = "No Data"
            if broker_history_df is not None:
                print(f"   > Got {len(broker_history_df)} days data.")
                last_5 = broker_history_df['NetTop3Vol'].tail(5).sum()
                summary_text = f"Net Volume (5d): {last_5:,.0f}"
                
            print("Generating Chart...")
            chart_path = generate_chart(ticker, ta_data['df_daily'], broker_history_df=broker_history_df)
            
            print("Running AI...")
            # Simple AI context prompt
            context = f"BANDAR MODE. {summary_text}"
            ai_res = get_ai_analysis(ticker, ta_data, news_summary=context)
            
            msg = f"🕵️ BANDAR REPORT: {ticker}\n{summary_text}\nAI: {str(ai_res)[:100]}..."
            broadcast_message(args.phone, msg, chart_path)
            print("Done.")
            return # Exit after bandar mode
            
        except Exception as e:
            print(f"Bandar Mode Error: {e}")
            sys.exit(1)

    # 1. Technical Analysis (Default Mode)
    try:
        print("Running Technical Analysis...")
        ta_data = analyze_technical(ticker)
        
        # 1.5 Quant Analysis (Real Bandarmology if available)
        goapi_key = os.getenv("GOAPI_API_KEY")
        broker_history_df = None
        
        if goapi_key and GoApiClient:
            print("Running Quant Analysis (GoAPI Real Data)...")
            client = GoApiClient(goapi_key)
            quant = QuantAnalyzer(client)
            
            real_bandar = quant.fetch_real_bandarmology(ticker)
            if real_bandar:
                print("   > Found Real Broker/Foreign Data!")
                bs_data = real_bandar.get('broker_summary', {})
                ff_data = real_bandar.get('foreign_flow', {})
                
                # Update Data (Always update summary if available, not just if non-neutral)
                ta_data['bandar_status'] = bs_data.get('status', 'Neutral')
                ta_data['bandar_action'] = f"Net Ratio: {bs_data.get('net_vol_ratio',0):.2f}"
                ta_data['bandar_summary'] = bs_data.get('summary', '-')
                ta_data['avg_bandar_price'] = f"{bs_data.get('avg_buy_price', 0):,.0f}"
                
                # Update Verdict
                tech_score = 50 
                if "Bullish" in ta_data['trend']: tech_score += 20
                if "Golden Cross" in ta_data['macd_status']: tech_score += 10
                
                final_res = quant.calculate_final_verdict(
                    tech_score=tech_score,
                    bandar_score=bs_data.get('bandar_score', 0),
                    foreign_score=ff_data.get('foreign_score', 0)
                )
                
                ta_data['final_score'] = final_res['final_score']
                ta_data['verdict'] = final_res['verdict']
                ta_data['foreign_status'] = ff_data.get('status', 'N/A')
            
            # 1.6 Historical Broker Summary (Optional)
            if args.include_history:
                print("Fetching Historical Broker Summary (may take 10-20s)...")
                # Fetch last 10-15 days reasonable for chart
                hist_raw = client.get_broker_summary_historical(ticker, days=15)
                broker_history_df = quant.analyze_historical_broker_summary(hist_raw)
                
                if broker_history_df is not None and not broker_history_df.empty:
                    print(f"   > Parsed {len(broker_history_df)} days of broker history.")
                    
                    # Add summary to AI context
                    last_5_net = broker_history_df['NetTop3Vol'].tail(5).sum()
                    status = "Accumulation" if last_5_net > 0 else "Distribution"
                    ta_data['bandar_history_summary'] = f"Historical (15d): {status} Trend. Net Top3 Vol (5d): {last_5_net:,.0f}"

    except Exception as e:
        print(f"Technical Analysis Failed: {e}")
        sys.exit(1)

    # 2. News Search (Catalyst)
    print("Running News Search (Serper)...")
    news_summary = fetch_stock_news(ticker)
    
    # 3. Chart Generation (Proof)
    print("Generating Chart...")
    # Pass broker_history_df to chart generator
    chart_path = generate_chart(ticker, ta_data['df_daily'], broker_history_df=broker_history_df)

    # 4. AI Analysis
    print("Running AI Technical Analysis (Gemini)...")
    ai_result = get_ai_analysis(ta_data['ticker'], ta_data, news_summary)
    
    # Handle AI Result (Dict or String)
    if isinstance(ai_result, dict):
        ai_analysis = ai_result.get('analysis', "Error parsing AI analysis.")
        # sentiment_score = ai_result.get('sentiment_score', 50) # Use if needed in future features
    else:
        # If it returns string but looks like a dict str, try to parse one last time
        import ast
        try:
            # Dangerous if untrusted, but usually okay for our own AI output
            parsed = json.loads(ai_result) if isinstance(ai_result, str) else None
            if not parsed and isinstance(ai_result, str) and ai_result.strip().startswith('{'):
                 parsed = json.loads(ai_result)
            
            if parsed and isinstance(parsed, dict):
                ai_analysis = parsed.get('analysis', str(ai_result))
            else:
                ai_analysis = str(ai_result)
        except:
            ai_analysis = str(ai_result)

    # 5. Format Message
    final_message = format_message(ta_data['ticker'], ta_data, ai_analysis, news_summary)

    # 6. Broadcast
    broadcast_message(args.phone, final_message, chart_path)

if __name__ == "__main__":
    main()
