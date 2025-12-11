import os
import requests
import subprocess
import threading
import json
import time
from dotenv import load_dotenv

# Import Logic
from technical_analysis import analyze_technical
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

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            try:
                print(message)
            except:
                pass

    def start_wa_service(self):
        """Starts Node.js service. Hides window for cleaner UX."""
        try:
            service_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "whatsapp-service")
            
            # Use CREATE_NO_WINDOW to hide the console completely
            # We will rely on the embedded QR code in the UI instead
            creation_flags = subprocess.CREATE_NO_WINDOW
            
            self.log("🚀 Memulai Layanan WhatsApp (Background)...")
            self.wa_process = subprocess.Popen(
                "npm start", 
                cwd=service_path,
                shell=True,
                creationflags=creation_flags
            )
        except Exception as e:
            self.log(f"❌ Gagal memulai Layanan WhatsApp: {e}")

    def stop_wa_service(self):
        if self.wa_process:
            try:
                subprocess.run(f"taskkill /F /T /PID {self.wa_process.pid}", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                try:
                    print(f"Error killing service: {e}")
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

    def run_analysis(self, ticker, progress_callback=None):
        """
        Orchestrates the full analysis pipeline.
        :param progress_callback: Function to update progress bar (0.0 - 1.0)
        """
        ticker = ticker.upper()
        self.log(f"🔵 Memulai Deep Dive untuk {ticker}...")
        if progress_callback: progress_callback(0.1)
        
        # Save to History
        db_manager.add_history(ticker)

        # 1. Check Cache
        cached_data = db_manager.get_cached_analysis(ticker)
        if cached_data:
            self.log("⚡ Menggunakan Data Cache (Hemat Token)...")
            if progress_callback: progress_callback(1.0)
            
            chart_filename = f"chart_{ticker}.jpg"
            # Note: chart path handling might need adjustment depending on where chart_generator saves it
            # For now, we assume it regenerates or we trust the path exists
            # To be safe, we might skip chart in cache or check existence
            return cached_data['full_message'], None # Cached chart path handling can be improved

        try:
            # 2. Technical Analysis
            self.log("📊 Menjalankan Analisa Teknikal...")
            if progress_callback: progress_callback(0.3)
            ta_data = analyze_technical(ticker)
            
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
            final_message = format_message(ta_data['ticker'], ta_data, ai_analysis, news_summary)
            
            # 7. Save
            db_manager.save_analysis(ta_data['ticker'], ta_data, ai_analysis, final_message)
            self.log("✅ Analisa Selesai.")
            if progress_callback: progress_callback(1.0)
            
            return final_message, chart_path
            
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

