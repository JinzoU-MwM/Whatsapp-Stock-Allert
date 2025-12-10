import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import sys
import os
import requests
import subprocess
from dotenv import load_dotenv

# Load env
load_dotenv()

# Import logic
sys.path.append(os.path.join(os.path.dirname(__file__), 'stock-intelligence'))
from technical_analysis import analyze_technical
from catalyst_agent import get_ai_analysis
from news_fetcher import fetch_stock_news
from chart_generator import generate_chart
from main import format_message, broadcast_message
import db_manager  # Import the new database manager

# Initialize DB on startup
db_manager.init_db()

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StockSignalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("StockSignal Intelligence (Antigravity Edition)")
        self.geometry("900x700")
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="StockSignal\nIntelligence", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Status: Siap (Idle)", text_color="gray")
        self.status_label.grid(row=1, column=0, padx=20, pady=10)

        # Main Content Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # 1. Input Section
        self.input_label = ctk.CTkLabel(self.main_frame, text="Kode Saham / Ticker (Contoh: BREN, DEWI)", font=ctk.CTkFont(size=14))
        self.input_label.pack(anchor="w", pady=(0, 5))

        self.ticker_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Masukkan Ticker...", width=300)
        self.ticker_entry.pack(anchor="w", pady=(0, 10))
        self.ticker_entry.bind('<Return>', self.start_analysis_thread)

        self.analyze_btn = ctk.CTkButton(self.main_frame, text="🚀 Analisa Lengkap (Deep Dive)", command=self.start_analysis_thread)
        self.analyze_btn.pack(anchor="w", pady=(0, 20))

        # 2. Console / Logs ("The Brain")
        self.console_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.console_frame.pack(fill="x", pady=(0, 5))
        
        self.console_label = ctk.CTkLabel(self.console_frame, text="Proses Berpikir AI (Logs)", font=ctk.CTkFont(size=14, weight="bold"))
        self.console_label.pack(side="left")
        
        self.group_btn = ctk.CTkButton(self.console_frame, text="🔍 Cari ID Grup WhatsApp", width=150, height=24, fg_color="#444", command=self.fetch_groups)
        self.group_btn.pack(side="right")

        self.console_textbox = ctk.CTkTextbox(self.main_frame, height=150)
        self.console_textbox.pack(fill="x", pady=(0, 20))
        self.console_textbox.configure(state="disabled")

        # 3. Preview Section
        self.preview_label = ctk.CTkLabel(self.main_frame, text="Preview Pesan WhatsApp", font=ctk.CTkFont(size=14, weight="bold"))
        self.preview_label.pack(anchor="w", pady=(0, 5))

        self.preview_textbox = ctk.CTkTextbox(self.main_frame, height=200)
        self.preview_textbox.pack(fill="both", expand=True, pady=(0, 10))

        # 4. Action Buttons
        self.actions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.actions_frame.pack(fill="x")

        self.send_btn = ctk.CTkButton(self.actions_frame, text="📲 Kirim ke WhatsApp", fg_color="green", hover_color="darkgreen", command=self.send_whatsapp, state="disabled")
        self.send_btn.pack(side="right")

        self.copy_btn = ctk.CTkButton(self.actions_frame, text="📋 Salin Teks", fg_color="gray", hover_color="darkgray", command=self.copy_to_clipboard)
        self.copy_btn.pack(side="right", padx=10)

        # Check Node.js Service
        self.check_service_health()
        
        # Start WhatsApp Service Management
        self.wa_process = None
        self.start_wa_service()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_wa_service(self):
        """Starts the Node.js WhatsApp service in a separate console window."""
        try:
            service_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp-service")
            auth_path = os.path.join(service_path, ".wwebjs_auth")
            
            # Determine creation flags
            # If auth exists, hide the window. If not, show it for QR scanning.
            creation_flags = subprocess.CREATE_NEW_CONSOLE
            if os.path.exists(auth_path):
                creation_flags = subprocess.CREATE_NO_WINDOW
                self.log("✅ Layanan WhatsApp dimulai di latar belakang (Terautentikasi).")
            else:
                self.log("✅ Layanan WhatsApp dimulai... (Scan QR di jendela baru)")
            
            # We use shell=True to find 'npm' easily
            self.wa_process = subprocess.Popen(
                "npm start", 
                cwd=service_path,
                shell=True,
                creationflags=creation_flags
            )
        except Exception as e:
            self.log(f"❌ Gagal memulai Layanan WhatsApp: {e}")

    def on_closing(self):
        """Kills the WhatsApp service process tree when the app is closed."""
        if self.wa_process:
            try:
                # Taskkill /T kills the process tree (cmd.exe -> npm -> node)
                subprocess.run(f"taskkill /F /T /PID {self.wa_process.pid}", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception as e:
                print(f"Error killing service: {e}")
        
        self.destroy()
        sys.exit(0)

    def log(self, message):
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", message + "\n")
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def check_service_health(self):
        def _check():
            try:
                requests.get("http://localhost:3000/health", timeout=2)
                self.status_label.configure(text="Sistem: ONLINE ✅", text_color="green")
            except:
                self.status_label.configure(text="Sistem: OFFLINE ❌", text_color="red")
                self.log("⚠️ Layanan WhatsApp tidak terdeteksi! Pastikan 'start_app.bat' berjalan benar.")
        
        threading.Thread(target=_check, daemon=True).start()

    def fetch_groups(self):
        self.log("🔍 Sedang mengambil daftar Grup WhatsApp...")
        def _fetch():
            try:
                response = requests.get("http://localhost:3000/groups", timeout=10)
                if response.status_code == 200:
                    groups = response.json()
                    if not groups:
                        self.log("⚠️ Tidak ada grup ditemukan.")
                        return
                    
                    self.log("\n=== DAFTAR GRUP WHATSAPP ===")
                    for g in groups:
                        self.log(f"📁 Nama: {g['name']}")
                        self.log(f"🔑 ID: {g['id']}")
                        self.log("-" * 30)
                    self.log("ℹ️ Salin ID (akhiran @g.us) ke file .env bagian TARGET_PHONE")
                else:
                    self.log(f"❌ Gagal mengambil grup: {response.text}")
            except Exception as e:
                self.log(f"❌ Error: {str(e)}")
        
        threading.Thread(target=_fetch, daemon=True).start()

    def start_analysis_thread(self, event=None):
        ticker = self.ticker_entry.get().strip()
        if not ticker:
            messagebox.showwarning("Input Error", "Masukkan kode saham terlebih dahulu.")
            return

        self.analyze_btn.configure(state="disabled")
        self.send_btn.configure(state="disabled")
        self.preview_textbox.delete("1.0", "end")
        self.console_textbox.configure(state="normal")
        self.console_textbox.delete("1.0", "end")
        self.console_textbox.configure(state="disabled")
        
        threading.Thread(target=self.run_analysis, args=(ticker,), daemon=True).start()

    def run_analysis(self, ticker):
        self.log(f"🔵 Memulai Deep Dive untuk {ticker.upper()}...")
        
        # 1. Check Cache
        cached_data = db_manager.get_cached_analysis(ticker.upper())
        if cached_data:
            self.log("⚡ Menggunakan Data Cache (Hemat Token)...")
            self.log(f"📅 Waktu Analisa: {cached_data['timestamp']}")
            
            final_message = cached_data['full_message']
            
            # Update UI
            self.preview_textbox.insert("end", final_message)
            self.send_btn.configure(state="normal")
            self.analyze_btn.configure(state="normal")
            
            # Restore chart path if exists
            chart_filename = f"chart_{ticker.upper()}.jpg"
            chart_path = os.path.join(os.getcwd(), "stock-intelligence", "charts", chart_filename)
            if os.path.exists(chart_path):
                self.current_chart_path = chart_path
                self.log(f"📊 Chart (Cache) siap dikirim.")
            else:
                self.current_chart_path = None
                
            self.log("✅ Analisa (Cache) Siap! Silakan review.")
            return

        try:
            # 2. Technical Analysis (Real-time)
            self.log("📊 Menjalankan Analisa Teknikal (Daily + Weekly)...")
            ta_data = analyze_technical(ticker.upper())
            self.log(f"✅ TA Selesai: Tren Daily={ta_data['trend']} | Weekly={ta_data['major_trend']}")

            # 3. News Fetching
            self.log("🌍 Mengambil Berita Real-Time (Serper)...")
            news_summary = fetch_stock_news(ta_data['ticker'])
            self.log("✅ Berita Terkumpul.")

            # 4. AI Analysis
            self.log("🧠 Melakukan Riset AI (Data + Berita)...")
            ai_analysis = get_ai_analysis(ta_data['ticker'], ta_data, news_summary)
            self.log("✅ Riset AI Selesai.")

            # 5. Chart Generation
            self.log("📈 Membuat Chart Candlestick...")
            chart_path = generate_chart(ta_data['ticker'], ta_data['df_daily'])
            if chart_path:
                self.log(f"✅ Chart disimpan: {os.path.basename(chart_path)}")

            # 6. Format Message
            final_message = format_message(ta_data['ticker'], ta_data, ai_analysis, news_summary)
            
            # 7. Save to Cache (Note: We don't cache the image path specifically, but it exists on disk)
            db_manager.save_analysis(ta_data['ticker'], ta_data, ai_analysis, final_message)
            self.log("💾 Data disimpan ke Database.")
            
            # Update UI
            self.preview_textbox.insert("end", final_message)
            self.send_btn.configure(state="normal")
            self.log("✨ Laporan & Chart Siap! Silakan review.")
            
            # Store chart path in instance for sending
            self.current_chart_path = chart_path

        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            messagebox.showerror("Analisa Gagal", str(e))
        finally:
            self.analyze_btn.configure(state="normal")

    def send_whatsapp(self):
        message = self.preview_textbox.get("1.0", "end").strip()
        phone = os.getenv("TARGET_PHONE")
        # Use chart path if available from this session
        chart_to_send = getattr(self, 'current_chart_path', None)
        
        if not phone:
            messagebox.showerror("Konfigurasi Error", "TARGET_PHONE tidak ditemukan di file .env")
            return
            
        self.log(f"📲 Mengirim ke {phone}...")
        
        def _send():
            try:
                broadcast_message(phone, message, chart_to_send)
                self.log("✅ Pesan & Gambar Berhasil Terkirim!")
                messagebox.showinfo("Sukses", "Pesan terkirim ke WhatsApp!")
            except Exception as e:
                self.log(f"❌ Gagal mengirim: {e}")
                messagebox.showerror("Gagal Kirim", str(e))

        threading.Thread(target=_send, daemon=True).start()

    def copy_to_clipboard(self):
        text = self.preview_textbox.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.log("📋 Teks disalin ke clipboard.")

if __name__ == "__main__":
    app = StockSignalApp()
    app.mainloop()
