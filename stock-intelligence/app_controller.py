import os
import requests
import subprocess
import threading
import json
import time
from dotenv import load_dotenv

# Import Logic
from technical_analysis import analyze_technical
from quant_engine import QuantAnalyzer
try:
    from goapi_client import GoApiClient
except ImportError:
    GoApiClient = None

from catalyst_agent import get_technical_analysis, get_bandarmology_analysis
from news_fetcher import fetch_stock_news
from chart_generator import generate_chart
from main import format_message, broadcast_message
import db_manager

class StockAppController:
    def __init__(self, log_callback=None):
        """
        :param log_callback: Function to send log messages to (e.g., ui_logger)
        """
        self.log_callback = log_callback
        self.wa_process = None
        self.service_url = "http://localhost:3000"
        
        load_dotenv()
        db_manager.init_db()
        
        # Initialize Quant Components
        self.goapi_client = None
        if os.getenv("GOAPI_API_KEY") and GoApiClient:
            self.goapi_client = GoApiClient()
            
        self.quant_engine = QuantAnalyzer(self.goapi_client)

    def log(self, message):
        # Suppress logging in production unless it's a critical error or analysis step
        if self.log_callback and (message.startswith("✅") or message.startswith("❌") or message.startswith("📊") or message.startswith("🧠") or message.startswith("🌍") or message.startswith("🔵") or message.startswith("🔎") or message.startswith("📈")):
             self.log_callback(message)
        # Always log to console/file if needed for debugging, or comment out for cleaner production
        # else:
        #     try:
        #         print(message)
        #     except:
        #         pass

    def start_wa_service(self):
        """Starts Node.js service. Hides window for cleaner UX but logs to file."""
        try:
            service_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whatsapp-service")
            log_path = os.path.join(service_path, "service_debug.log")
            
            # Use CREATE_NO_WINDOW to hide the console completely
            creation_flags = subprocess.CREATE_NO_WINDOW
            
            self.log(f"🚀 Memulai Layanan WhatsApp (Log: {log_path})...")
            
            # Open log file
            self.log_file = open(log_path, "w")
            
            # Use node directly instead of npm for better process control
            cmd = "node index.js"
            
            self.wa_process = subprocess.Popen(
                cmd, 
                cwd=service_path,
                shell=True,
                creationflags=creation_flags,
                stdout=self.log_file,
                stderr=self.log_file
            )
        except Exception as e:
            self.log(f"❌ Gagal memulai Layanan WhatsApp: {e}")

    def stop_wa_service(self):
        if self.wa_process:
            try:
                subprocess.run(f"taskkill /F /T /PID {self.wa_process.pid}", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                pass
        
        if hasattr(self, 'log_file') and self.log_file:
            try:
                self.log_file.close()
            except:
                pass

    def check_service_health(self):
        try:
            requests.get(f"{self.service_url}/health", timeout=2)
            return True
        except:
            return False

    def get_qr_code(self):
        """Fetches QR code string from the Node.js service."""
        try:
            response = requests.get(f"{self.service_url}/qr", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data
            return None
        except:
            return None

    def logout_whatsapp(self):
        try:
            response = requests.post(f"{self.service_url}/logout", timeout=5)
            if response.status_code == 200:
                self.log("✅ Berhasil Logout WhatsApp.")
                return True
            else:
                self.log(f"⚠️ Gagal Logout: {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error during logout: {e}")
            return False

    def fetch_groups(self):
        try:
            response = requests.get(f"{self.service_url}/groups", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception as e:
            self.log(f"Error fetching groups: {e}")
            return []

    def run_analysis(self, ticker, timeframe="daily", progress_callback=None):
        """
        Orchestrates the unified "Stock Intelligence" pipeline.
        Combines Technical, Forensic Bandarmology, and News into one report.
        """
        ticker = ticker.upper()
        self.log(f"🔵 Memulai Stock Intelligence untuk {ticker} ({timeframe})...")
        if progress_callback: progress_callback(0.1)
        
        # Save to History
        db_manager.add_history(ticker)

        _cached = None
        # 1. Check Cache (Daily only)
        if timeframe == "daily":
            cached_data = db_manager.get_cached_analysis(ticker)
            if cached_data:
                # We can return cached, but let's see if we want to force refresh for demo
                # self.log("⚡ Menggunakan Data Cache (Hemat Token)...")
                # if progress_callback: progress_callback(1.0)
                # return cached_data['full_message'], None, 50 # TODO: store sentiment
                pass 

        try:
            # PARALLEL EXECUTION WRAPPER
            # We fetch Tech, Bandarmology, and News concurrently to save time.
            
            import concurrent.futures
            
            def fetch_full_bandar():
                """Helper to fetch all required bandarmology data if eligible"""
                if self.goapi_client and timeframe == "daily":
                    self.log(f"🔎 Menjalankan Forensik Bandarmology...")
                    if progress_callback: progress_callback(0.4) # Approx
                    real = self.quant_engine.fetch_real_bandarmology(ticker)
                    hist = self.goapi_client.get_broker_summary_historical(ticker, days=20)
                    return real, hist
                return None, None

            # Execute Parallel Tasks
            with concurrent.futures.ThreadPoolExecutor() as executor:
                self.log(f"🚀 Memulai Parallel Data Fetching ({ticker})...")
                
                # 1. Technical
                future_tech = executor.submit(analyze_technical, ticker, timeframe=timeframe)
                
                # 2. Bandarmology
                future_bandar = executor.submit(fetch_full_bandar)
                
                # 3. News
                future_news = executor.submit(fetch_stock_news, ticker)
                
                # WAIT FOR RESULTS
                try:
                    ta_data = future_tech.result()
                    real_bandar, hist_raw = future_bandar.result()
                    news_summary = future_news.result()
                except Exception as e:
                    self.log(f"❌ Error in Parallel Fetch: {e}")
                    raise e

            # Progress Update
            if progress_callback: progress_callback(0.6)

            # Variables for Bandarmology Logic
            broker_history_df = None
            broker_flow_df = None
            bandar_summary_lines = []
            
            # Context for AI
            context_data = {
                'today_summary': 'N/A',
                'top_seller': 'N/A',
                'seller_hist_net': 'N/A',
                'seller_avg_price': '0',
                'vwap': ta_data.get('vwap', 0),
                'price_change': ta_data.get('change_pct', 0),
                'top1_buy_price': 0,
                'top1_sell_price': 0,
                'status_header': 'N/A' 
            }

            # PROCESS BANDARMOLOGY DATA (If fetched)
            if real_bandar and hist_raw:
                # A. Real-Time Snapshot
                bs_data = real_bandar.get('broker_summary', {})
                ff_data = real_bandar.get('foreign_flow', {})
                context_data['today_summary'] = bs_data.get('summary', 'N/A')
                
                # Update Base TA Data
                ta_data['bandar_status'] = bs_data.get('status', 'Neutral')
                ta_data['foreign_status'] = ff_data.get('status', 'N/A')
                
                # B. Historical & Cumulative Analysis
                # Process the fetched history
                broker_history_df = self.quant_engine.analyze_historical_broker_summary(hist_raw)
                cum_summary = self.quant_engine.get_cumulative_broker_summary(hist_raw)
                
                # Chart Data: Broker Flow
                broker_flow_df = self.quant_engine.prepare_broker_flow_data(hist_raw)
                
                # Identify Focus Broker (Cumulative Top Seller)
                top_seller_code = "N/A"
                if cum_summary['top_sellers']:
                    top_seller_code = cum_summary['top_sellers'][0][0]
                elif bs_data.get('top_seller'):
                    top_seller_code = bs_data.get('top_seller')
                
                context_data['top_seller'] = top_seller_code
                
                # Extract Top 1 Prices (Available in bs_data from QuantEngine update)
                context_data['top1_buy_price'] = bs_data.get('top1_buy_price', 0)
                context_data['top1_sell_price'] = bs_data.get('top1_sell_price', 0)
                
                if top_seller_code != "N/A":
                    net_vol, avg_price = self.quant_engine.calculate_broker_net_history(hist_raw, top_seller_code)
                    pos_str = "Net Buy" if net_vol > 0 else "Net Sell"
                    context_data['seller_hist_net'] = f"{pos_str} ({net_vol:,.0f} Lot)"
                    context_data['seller_avg_price'] = f"{avg_price:,.0f}"

                # Update Verdict Score (Quant + Tech)
                # Tech Score approximation
                tech_score = 50 
                if "Bullish" in ta_data['trend']: tech_score += 20
                if "Golden Cross" in ta_data['macd_status']: tech_score += 10
                
                final_res = self.quant_engine.calculate_final_verdict(
                    tech_score=tech_score,
                    bandar_score=bs_data.get('bandar_score', 0),
                    foreign_score=ff_data.get('foreign_score', 0)
                )
                ta_data['final_score'] = final_res['final_score']
                ta_data['verdict'] = final_res['verdict']

                # Prepare Summary Lines for Message
                if broker_history_df is not None and not broker_history_df.empty:
                    last_day = broker_history_df.iloc[-1]
                    bandar_summary_lines.append(f"Top Buyer: {last_day.get('Top3Buyers', '-')}")
                    bandar_summary_lines.append(f"Top Seller: {last_day.get('Top3Sellers', '-')}")

            # News Logging (Already fetched)
            self.log("🌍 Berita Terambil via Parallel Fetch.")
            
            # 4. AI Agents (Dual Core - Parallel)
            self.log("🧠 Melakukan Riset AI (Forensic & Technical) via Parallel Agents...")
            
            with concurrent.futures.ThreadPoolExecutor() as ai_executor:
                future_ai_tech = ai_executor.submit(get_technical_analysis, ta_data['ticker'], ta_data, news_summary)
                # Only run forensic if context exists, but we can submit it anyway and handle inside or guard here
                if context_data.get('top_seller') != 'N/A' or context_data.get('today_summary') != 'N/A':
                    future_ai_forensic = ai_executor.submit(get_bandarmology_analysis, ta_data['ticker'], context_data)
                else:
                    # Mock future if no bandar data (rare for IDX)
                    future_ai_forensic = None
                
                try:
                    ai_tech = future_ai_tech.result()
                    if future_ai_forensic:
                        ai_forensic = future_ai_forensic.result()
                    else:
                        ai_forensic = {"status": "N/A", "analysis": "Data Bandar Tidak Cukup"}
                except Exception as e:
                    self.log(f"❌ Error in Parallel AI: {e}")
                    ai_tech = {'analysis': f"Error: {e}", 'action': 'ERROR'}
                    ai_forensic = {}
            
            if progress_callback: progress_callback(0.8)
            
            # 5. Chart Generation (Technical Standard)
            self.log("📈 Membuat Chart Technical Standard...")
            
            # User requested to "remove broker chart and bring back technical chart"
            # So we stick to chart_mode='technical' even if we have broker flow data.
            chart_path = generate_chart(
                ta_data['ticker'], 
                ta_data['df_daily'], 
                broker_history_df=broker_history_df,
                broker_flow_df=broker_flow_df,
                chart_mode='technical' 
            )
            
            # 6. Formatting The Report (STOCK INTELLIGENCE Template)
            
            # Extract AI Contents
            tech_analysis_text = ai_tech.get('analysis', str(ai_tech)) if isinstance(ai_tech, dict) else str(ai_tech)
            trading_plan = ai_tech.get('trading_plan', {})
            tech_action = ai_tech.get('action', 'WAIT_AND_SEE')
            
            forensic_status = ai_forensic.get('status', 'NETRAL') if isinstance(ai_forensic, dict) else 'NETRAL'
            forensic_analysis = ai_forensic.get('analysis', '-') if isinstance(ai_forensic, dict) else '-'
            forensic_warning = ai_forensic.get('warning', '') if isinstance(ai_forensic, dict) else ''
            
            # Build Sections
            
            # Header
            msg = f"🚨 *STOCK INTELLIGENCE: {ticker}*\n"
            msg += f"🎯 *VERDICT: {tech_action}* (Conf: {ta_data.get('final_score',0)}%)\n"
            msg += f"Harga: {ta_data['price']:.0f} 📉\n\n"
            
            # Section 1: Data Teknikal
            msg += "📊 *DATA TEKNIKAL & VOLUME FLOW*\n"
            msg += f"* Tren: {ta_data['trend']}\n"
            msg += f"* Candle: {ta_data.get('candle_pattern', '-')}\n"
            msg += f"* MACD: {ta_data['macd_status']}\n"
            msg += f"* Volume: {ta_data['vol_status']} (Ratio: {ta_data['vol_ratio']:.2f}x)\n"
            msg += f"* Foreign Flow: {ta_data.get('foreign_status', '-')}\n"
            msg += f"* Bandar Status: {ta_data.get('bandar_status', '-')}\n"
            msg += f"* Detail: {bandar_summary_lines[0] if bandar_summary_lines else '-'} vs {bandar_summary_lines[1] if len(bandar_summary_lines)>1 else '-'}\n"
            msg += f"* RSI: {ta_data['rsi']:.2f} | ADX: {ta_data.get('adx',0):.2f}\n\n"
            
            # Section 2: Fundamental
            val = ta_data.get('valuation', {})
            msg += "💰 *FUNDAMENTAL & VALUASI*\n"
            msg += f"* Status: {val.get('valuation_status', '-')}\n"
            msg += f"* PER: {val.get('per',0):.2f}x | PBV: {val.get('pbv',0):.2f}x\n"
            # Market Cap Formatting
            mc_val = val.get('market_cap', 0)
            mc_str = "0 M"
            if mc_val > 1_000_000_000_000: # Trillion
                mc_str = f"{mc_val/1e12:.2f} T (IDR)"
            else:
                mc_str = f"{mc_val/1e9:.0f} M (IDR)"
            
            msg += f"* ROE: {val.get('roe',0)*100:.2f}% | MarCap: {mc_str}\n\n"
            
            msg += "📣 *SYSTEM SCAN: MARKET INTELLIGENCE*\n\n"
            
            # Section 3: Analisa Struktur (Technical Agent)
            msg += "1️⃣ *ANALISA STRUKTUR CHART*\n"
            msg += f"* Trend: {ta_data['trend']}\n"
            msg += f"* Key Levels:\n  - Support: {ta_data['support']:.0f}\n  - Resistance: {ta_data['resistance']:.0f}\n"
            if "pivot" in ta_data: msg += f"  - Pivot: {ta_data['pivot']:.0f}\n"
            msg += "* Analisa Teknikal:\n"
            msg += f"\"{tech_analysis_text}\"\n\n"
            
            # Section 4: Bandarmology Forensic
            msg += "2️⃣ *BANDARMOLOGY (FORENSIC)*\n"
            msg += f"* Status: {forensic_status}\n"
            if bandar_summary_lines:
                msg += f"* Peta Kekuatan:\n{bandar_summary_lines[0]}\n{bandar_summary_lines[1]}\n"
            msg += f"* Insight: {forensic_analysis}\n"
            if forensic_warning:
                msg += f"⚠️ *WARNING: {forensic_warning}*\n"
            msg += "\n"
            
            # Section 5: Trading Plan
            msg += "🎯 *TRADING PLAN & EXECUTION*\n"
            if trading_plan:
                msg += f"✅ *ENTRY IDEAL*: {trading_plan.get('buy_area', '-')}\n"
                msg += f"💸 *TARGET PRICE*: {trading_plan.get('target_profit', '-')}\n"
                msg += f"❎ *STOP LOSS*: {trading_plan.get('stop_loss', '-')}\n"
            else:
                msg += "Waiting for clear setup.\n"
            msg += f"📉 *RISK-REWARD*: Calculated by Pivot\n\n"
            
            # Section 6: Sentimen Berita
            msg += "🌍 *SENTIMEN BERITA (Update):*\n"
            if news_summary:
                # Truncate news to first 3 lines/bullets
                news_lines = news_summary.split('\n')
                msg += "\n".join(news_lines[:5])
            else:
                msg += "- Tidak ada berita signifikan terbaru."
                
            msg += "\n\nDibuat oleh StockSignal Bot"
            
            # Save (Daily)
            if timeframe == "daily":
                db_manager.save_analysis(ta_data['ticker'], ta_data, tech_analysis_text, msg)
            
            self.log("✅ Analisa Selesai.")
            if progress_callback: progress_callback(1.0)
            
            return msg, chart_path, ta_data.get('final_score', 50)
            
        except Exception as e:
            self.log(f"❌ Error during analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

    def send_whatsapp_message(self, phone, message, image_path=None):
        broadcast_message(phone, message, image_path)
        
        # Cleanup chart image if it exists to save storage
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                self.log(f"🗑️ Chart dihapus: {os.path.basename(image_path)}")
            except Exception as e:
                self.log(f"⚠️ Gagal menghapus chart: {e}")

    # --- HISTORY & FAVORITES ---
    def get_history(self, limit=10):
        return db_manager.get_history(limit)

    def get_favorites(self):
        return db_manager.get_favorites()

    def add_favorite(self, ticker):
        if db_manager.add_favorite(ticker):
            self.log(f"⭐ {ticker} ditambahkan ke Favorit.")
            return True
        return False

    def remove_favorite(self, ticker):
        db_manager.remove_favorite(ticker)
        self.log(f"🗑️ {ticker} dihapus dari Favorit.")

    def is_favorite(self, ticker):
        return db_manager.is_favorite(ticker)

    # --- PORTFOLIO MANAGEMENT ---
    def get_portfolio(self):
        return db_manager.get_portfolio()

    def add_portfolio_item(self, ticker, price, lots):
        """
        Adds item to portfolio with Weighted Average logic.
        Formula: New Avg = ((Old Avg * Old Lots) + (New Price * New Lots)) / (Old Lots + New Lots)
        """
        ticker = ticker.upper()
        
        # 1. Check if exists
        existing = db_manager.get_portfolio_item(ticker)
        
        final_price = price
        final_lots = lots
        
        if existing:
            old_price = existing['avg_price']
            old_lots = existing['lots']
            
            total_lots = old_lots + lots
            
            # Prevent division by zero if someone enters negative lots (selling)
            if total_lots > 0:
                weighted_avg = ((old_price * old_lots) + (price * lots)) / total_lots
                final_price = weighted_avg
                final_lots = total_lots
                self.log(f"📉 Averaging Down/Up for {ticker}: Old {old_price:,.0f} -> New {final_price:,.0f}")
            elif total_lots == 0:
                # Sold everything
                return self.remove_portfolio_item(ticker)
            else:
                self.log(f"⚠️ Cannot have negative lots for {ticker}")
                return False

        if db_manager.add_portfolio(ticker, final_price, final_lots):
            self.log(f"💼 Portfolio Saved: {ticker} @ {final_price:,.0f} (Qty: {final_lots})")
            return True
        return False

    def remove_portfolio_item(self, ticker):
        if db_manager.delete_portfolio(ticker):
            self.log(f"🗑️ Removed {ticker} from Portfolio.")
            return True
        return False

    def get_portfolio_summary(self):
        """Returns portfolio list with added Real-Time P/L data."""
        portfolio = self.get_portfolio()
        if not portfolio:
            return []

        self.log("💼 Calculating Portfolio Performance...")
        import yfinance as yf
        
        # Prepare Tickers for Bulk Fetch (Add .JK)
        yf_tickers = [p['ticker'] + ".JK" for p in portfolio]
        if not yf_tickers:
            return portfolio

        try:
            # Efficient Bulk Fetch
            tickers_str = " ".join(yf_tickers)
            # Use '1d' history to get the absolute latest close
            data = yf.download(tickers_str, period="1d", progress=False)['Close']
            
            # Handle single ticker result (Series) vs multiple (DataFrame)
            is_series = len(yf_tickers) == 1
            
            for item in portfolio:
                sym = item['ticker'] + ".JK"
                current_price = 0
                
                try:
                    if is_series:
                        if not data.empty:
                            current_price = float(data.iloc[-1])
                    else:
                        if sym in data.columns:
                            # access last row for that symbol
                            val = data[sym].iloc[-1]
                            current_price = float(val)
                except Exception as e:
                    self.log(f"⚠️ Price fetch error for {sym}: {e}")

                # Calculations
                # 1 Lot = 100 Shares (Standard IDX)
                item['current_price'] = current_price
                
                if current_price > 0:
                    initial_investment = item['avg_price'] * item['lots'] * 100
                    current_market_val = current_price * item['lots'] * 100
                    
                    pl_value = current_market_val - initial_investment
                    pl_pct = (pl_value / initial_investment) * 100 if initial_investment != 0 else 0
                    
                    item['market_value'] = current_market_val
                    item['pl_value'] = pl_value
                    item['pl_pct'] = pl_pct
                else:
                    item['market_value'] = 0
                    item['pl_value'] = 0
                    item['pl_pct'] = 0

        except Exception as e:
            self.log(f"❌ Portfolio Analysis Error: {e}")
            
        return portfolio

    # --- SETTINGS / CONFIG ---
    def get_config(self):
        """Reads current environment variables useful for UI."""
        return {
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
            "SERPER_API_KEY": os.getenv("SERPER_API_KEY", ""),
            "GOAPI_API_KEY": os.getenv("GOAPI_API_KEY", ""),
            "TARGET_PHONE": os.getenv("TARGET_PHONE", ""),
            "AI_MODEL": os.getenv("AI_MODEL", "gemini-2.0-flash-exp") # Default to fast free model
        }

    def save_config(self, config_dict):
        """Writes configuration to .env file and updates current environment."""
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        
        try:
            # 1. Read existing lines to preserve comments if possible, or just overwrite simple
            # For simplicity and robustness, we'll read, update known keys, and write back.
            
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    lines = f.readlines()
            
            # Map of keys to update
            keys_to_update = {
                "GOOGLE_API_KEY": config_dict.get("GOOGLE_API_KEY"),
                "SERPER_API_KEY": config_dict.get("SERPER_API_KEY"),
                "GOAPI_API_KEY": config_dict.get("GOAPI_API_KEY"),
                "TARGET_PHONE": config_dict.get("TARGET_PHONE"),
                "AI_MODEL": config_dict.get("AI_MODEL")
            }
            
            new_lines = []
            processed_keys = set()
            
            for line in lines:
                key_match = None
                for key in keys_to_update:
                    if line.startswith(f"{key}="):
                        key_match = key
                        break
                
                if key_match:
                    val = keys_to_update[key_match]
                    if val is not None:
                        new_lines.append(f"{key_match}={val}\n")
                        processed_keys.add(key_match)
                    else:
                        new_lines.append(line) # Keep as is if None passed
                else:
                    new_lines.append(line)
            
            # Append missing keys
            for key, val in keys_to_update.items():
                if key not in processed_keys and val is not None:
                    if new_lines and not new_lines[-1].endswith("\n"):
                        new_lines.append("\n")
                    new_lines.append(f"{key}={val}\n")
            
            # Write back
            with open(env_path, "w") as f:
                f.writelines(new_lines)
                
            # Update current process env
            for key, val in keys_to_update.items():
                if val:
                    os.environ[key] = val
            
            # Reload dotenv to be sure
            load_dotenv(override=True)
            
            # --- HOT RELOAD COMPONENTS ---
            # Re-initialize GoAPI Client and Quant Engine with new keys
            if os.getenv("GOAPI_API_KEY") and GoApiClient:
                self.log("🔄 Reloading GoAPI Client & Quant Engine...")
                self.goapi_client = GoApiClient()
                self.quant_engine = QuantAnalyzer(self.goapi_client)
            else:
                self.goapi_client = None
                self.quant_engine = QuantAnalyzer(None)
            
            self.log("✅ Configuration saved to .env")
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to save config: {e}")
            return False
