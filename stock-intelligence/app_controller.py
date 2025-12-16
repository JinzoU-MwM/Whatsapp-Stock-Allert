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

from catalyst_agent import get_ai_analysis
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
        if self.log_callback and (message.startswith("✅") or message.startswith("❌") or message.startswith("📊") or message.startswith("🧠") or message.startswith("🌍")):
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
        Orchestrates the full analysis pipeline.
        :param progress_callback: Function to update progress bar (0.0 - 1.0)
        """
        ticker = ticker.upper()
        self.log(f"🔵 Memulai Deep Dive untuk {ticker} ({timeframe})...")
        if progress_callback: progress_callback(0.1)
        
        # Save to History
        db_manager.add_history(ticker)

        # 1. Check Cache (Skip for now if timeframe is not standard, or implement better cache key)
        # For simplicity, we only cache daily default. If timeframe != daily, skip cache or update cache key.
        # Let's simple skip cache for non-daily for now to ensure freshness.
        if timeframe == "daily":
            cached_data = db_manager.get_cached_analysis(ticker)
            if cached_data:
                self.log("⚡ Menggunakan Data Cache (Hemat Token)...")
                if progress_callback: progress_callback(1.0)
                return cached_data['full_message'], None

        try:
            # 2. Technical Analysis
            self.log(f"📊 Menjalankan Analisa Teknikal ({timeframe})...")
            if progress_callback: progress_callback(0.3)
            ta_data = analyze_technical(ticker, timeframe=timeframe)
            
            # 2.1 Quant Analysis (Real Bandarmology if available)
            # Only run if we have GoAPI and timeframe is daily
            if self.goapi_client and timeframe == "daily":
                real_bandar = self.quant_engine.fetch_real_bandarmology(ticker)
                if real_bandar:
                    self.log(f"🔎 Mengambil Data Bandar Asli (GoAPI)...")
                    
                    # Merge scores
                    bs_data = real_bandar.get('broker_summary', {})
                    ff_data = real_bandar.get('foreign_flow', {})
                    
                    # Update TA Data with Real Info
                    # Always update if we have valid dictionary response, not just if status != Neutral
                    # The previous check `if bs_data.get('status') != "Neutral":` was filtering out valid "Neutral" or "Distribusi Ringan" data
                    
                    ta_data['bandar_status'] = bs_data.get('status', 'Neutral')
                    ta_data['bandar_action'] = f"Net Ratio: {bs_data.get('net_vol_ratio',0):.2f}"
                    ta_data['bandar_summary'] = bs_data.get('summary', '-')
                    
                    # Recalculate Final Verdict using Real Scores
                    # Extract current tech score proxy (approximate back from final score logic or re-calculate)
                    # For simplicity, we trust the quant_engine's full calculator if we were to move logic there.
                    # But since verdict logic is currently inside technical_analysis.py, we will patching it here.
                    
                    # Let's use QuantAnalyzer's verdict calculation to be authoritative
                    # Tech Score approximation from TA logic:
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
                    ta_data['foreign_status'] = ff_data.get('status', 'N/A') # Add new field

            # 3. News Fetching
            self.log("🌍 Mengambil Berita Real-Time...")
            if progress_callback: progress_callback(0.5)
            news_summary = fetch_stock_news(ta_data['ticker'])
            
            # 4. AI Analysis
            self.log("🧠 Melakukan Riset AI...")
            if progress_callback: progress_callback(0.7)
            ai_analysis = get_ai_analysis(ta_data['ticker'], ta_data, news_summary)
            
            # 5. Chart Generation
            self.log("📈 Membuat Chart...")
            if progress_callback: progress_callback(0.8)
            chart_path = generate_chart(ta_data['ticker'], ta_data['df_daily'])
            
            # 6. Formatting
            ai_text = ai_analysis
            sentiment_score = 50
            if isinstance(ai_analysis, dict):
                ai_text = ai_analysis.get('analysis', '')
                sentiment_score = ai_analysis.get('sentiment_score', 50)
            
            final_message = format_message(ta_data['ticker'], ta_data, ai_text, news_summary)
            
            # 7. Save (Only daily to DB for now to avoid schema change complexity)
            if timeframe == "daily":
                db_manager.save_analysis(ta_data['ticker'], ta_data, ai_text, final_message)
            
            self.log("✅ Analisa Selesai.")
            if progress_callback: progress_callback(1.0)
            
            return final_message, chart_path, sentiment_score
            
        except Exception as e:
            self.log(f"❌ Error during analysis: {str(e)}")
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

