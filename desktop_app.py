import customtkinter as ctk
from tkinter import messagebox
import threading
import sys
import os
import time
from PIL import Image
import qrcode

# Import Controller
sys.path.append(os.path.join(os.path.dirname(__file__), 'stock-intelligence'))
from app_controller import StockAppController

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StockSignalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("StockSignal Intelligence (Antigravity Edition)")
        self.geometry("950x750")

        # Initialize Controller
        self.controller = StockAppController(log_callback=self.log_ui)
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # UI Setup
        self.setup_sidebar()
        self.setup_main_area()
        
        # State
        self.current_chart_path = None
        self.qr_window = None
        
        # Startup Checks
        self.check_api_keys()
        self.controller.start_wa_service()
        self.check_service_health()
        
        # Start QR Polling
        self.after(3000, self.poll_qr_code)
        
        # Initial List Load
        self.update_sidebar_lists()
        
        # Cleanup on exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Spacer

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="StockSignal\nIntelligence", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Status: Init...", text_color="gray")
        self.status_label.grid(row=1, column=0, padx=20, pady=10)
        
        # QR Button
        self.qr_btn = ctk.CTkButton(self.sidebar_frame, text="📱 Scan QR WhatsApp", command=self.show_qr_modal, fg_color="#333")
        self.qr_btn.grid(row=2, column=0, padx=20, pady=10)
        
        # Logout Button (initially hidden)
        self.logout_btn = ctk.CTkButton(self.sidebar_frame, text="🚪 Logout WhatsApp", command=self.logout_whatsapp, fg_color="#800000", hover_color="red")
        self.logout_btn.grid(row=2, column=0, padx=20, pady=10)
        self.logout_btn.grid_remove()

        # Favorites Section
        self.fav_label = ctk.CTkLabel(self.sidebar_frame, text="⭐ Favorit:", font=ctk.CTkFont(size=14, weight="bold"))
        self.fav_label.grid(row=3, column=0, padx=20, pady=(20, 5), sticky="w")

        self.fav_frame = ctk.CTkScrollableFrame(self.sidebar_frame, width=160, height=200)
        self.fav_frame.grid(row=4, column=0, padx=10, pady=5)
        
        # History Section
        self.hist_label = ctk.CTkLabel(self.sidebar_frame, text="🕒 Riwayat:", font=ctk.CTkFont(size=14, weight="bold"))
        self.hist_label.grid(row=5, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.hist_frame = ctk.CTkScrollableFrame(self.sidebar_frame, width=160, height=150)
        self.hist_frame.grid(row=6, column=0, padx=10, pady=5)

    def update_sidebar_lists(self):
        # Refresh Favorites
        for widget in self.fav_frame.winfo_children():
            widget.destroy()
            
        favorites = self.controller.get_favorites()
        if not favorites:
            ctk.CTkLabel(self.fav_frame, text="Belum ada favorit", text_color="gray").pack()
        else:
            for ticker in favorites:
                # Row frame
                row = ctk.CTkFrame(self.fav_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                # Ticker Button (Load)
                btn = ctk.CTkButton(row, text=ticker, width=100, fg_color="#444", 
                                  command=lambda t=ticker: self.load_ticker(t))
                btn.pack(side="left", padx=2)
                
                # Delete Button
                del_btn = ctk.CTkButton(row, text="X", width=20, fg_color="#800000", hover_color="red",
                                      command=lambda t=ticker: self.remove_favorite(t))
                del_btn.pack(side="right", padx=2)

        # Refresh History
        for widget in self.hist_frame.winfo_children():
            widget.destroy()
            
        history = self.controller.get_history(limit=15)
        if not history:
            ctk.CTkLabel(self.hist_frame, text="Belum ada riwayat", text_color="gray").pack()
        else:
            for ticker in history:
                btn = ctk.CTkButton(self.hist_frame, text=ticker, fg_color="transparent", border_width=1,
                                  command=lambda t=ticker: self.load_ticker(t))
                btn.pack(fill="x", pady=2)

    def load_ticker(self, ticker):
        self.ticker_entry.delete(0, "end")
        self.ticker_entry.insert(0, ticker)
        self.update_favorite_btn_state(ticker)
        # Optional: Auto start analysis? Maybe not, let user decide.
        # self.start_analysis_thread()

    def add_favorite(self):
        ticker = self.ticker_entry.get().strip().upper()
        if ticker:
            if self.controller.add_favorite(ticker):
                self.update_sidebar_lists()
                self.update_favorite_btn_state(ticker)

    def remove_favorite(self, ticker):
        self.controller.remove_favorite(ticker)
        self.update_sidebar_lists()
        # If current input matches, update button state
        current = self.ticker_entry.get().strip().upper()
        if current == ticker:
            self.update_favorite_btn_state(current)

    def update_favorite_btn_state(self, ticker):
        if not ticker:
            self.fav_action_btn.configure(state="disabled", text="⭐")
            return
            
        self.fav_action_btn.configure(state="normal")
        if self.controller.is_favorite(ticker):
            self.fav_action_btn.configure(text="★ Favorit", fg_color="gold", text_color="black", command=lambda: self.remove_favorite(ticker))
        else:
            self.fav_action_btn.configure(text="☆ Add Fav", fg_color="transparent", text_color="white", command=self.add_favorite)

    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # 1. Input Section
        self.input_label = ctk.CTkLabel(self.main_frame, text="Kode Saham / Ticker (Contoh: BREN, DEWI)", font=ctk.CTkFont(size=14))
        self.input_label.pack(anchor="w", pady=(0, 5))

        # Input Row Frame
        input_row = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_row.pack(anchor="w", fill="x", pady=(0, 10))

        self.ticker_entry = ctk.CTkEntry(input_row, placeholder_text="Masukkan Ticker...", width=300)
        self.ticker_entry.pack(side="left", padx=(0, 10))
        self.ticker_entry.bind('<Return>', self.start_analysis_thread)
        self.ticker_entry.bind('<KeyRelease>', lambda e: self.update_favorite_btn_state(self.ticker_entry.get().strip().upper()))

        # Favorite Toggle Button
        self.fav_action_btn = ctk.CTkButton(input_row, text="☆ Add Fav", width=100, command=self.add_favorite)
        self.fav_action_btn.pack(side="left")

        # Timeframe Selection Frame
        self.timeframe_var = ctk.StringVar(value="daily")
        timeframe_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        timeframe_frame.pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(timeframe_frame, text="Timeframe:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        
        self.tf_daily = ctk.CTkRadioButton(timeframe_frame, text="Daily", variable=self.timeframe_var, value="daily")
        self.tf_daily.pack(side="left", padx=10)
        
        self.tf_weekly = ctk.CTkRadioButton(timeframe_frame, text="Weekly", variable=self.timeframe_var, value="weekly")
        self.tf_weekly.pack(side="left", padx=10)
        
        self.tf_monthly = ctk.CTkRadioButton(timeframe_frame, text="Monthly", variable=self.timeframe_var, value="monthly")
        self.tf_monthly.pack(side="left", padx=10)

        self.analyze_btn = ctk.CTkButton(self.main_frame, text="🚀 Analisa Lengkap (Deep Dive)", command=self.start_analysis_thread)
        self.analyze_btn.pack(anchor="w", pady=(0, 10))

        # Sentiment Meter (New)
        sentiment_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        sentiment_frame.pack(anchor="w", fill="x", pady=(0, 5))
        ctk.CTkLabel(sentiment_frame, text="Sentiment Score:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        self.sentiment_label = ctk.CTkLabel(sentiment_frame, text="N/A", font=ctk.CTkFont(size=12))
        self.sentiment_label.pack(side="left", padx=5)
        
        self.sentiment_bar = ctk.CTkProgressBar(self.main_frame, width=300, progress_color="gray")
        self.sentiment_bar.pack(anchor="w", pady=(0, 10))
        self.sentiment_bar.set(0.5) # Default 50%

        # Progress Bar (Analysis)
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=300)
        self.progress_bar.pack(anchor="w", pady=(0, 20))
        self.progress_bar.set(0)

        # 2. Console / Logs
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

    # --- LOGIC & BINDINGS ---

    def log_ui(self, message):
        """Callback for Controller to log to UI"""
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", message + "\n")
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def check_api_keys(self):
        missing = []
        if not os.getenv("GOOGLE_API_KEY"): missing.append("GOOGLE_API_KEY")
        if not os.getenv("SERPER_API_KEY"): missing.append("SERPER_API_KEY")
        
        if missing:
            msg = f"⚠️ API Key Hilang:\n{', '.join(missing)}\n\nSilakan lengkapi file .env"
            self.after(1000, lambda: messagebox.showwarning("Konfigurasi Belum Lengkap", msg))

    def check_service_health(self):
        def _check():
            is_healthy = self.controller.check_service_health()
            if is_healthy:
                self.status_label.configure(text="Sistem: ONLINE ✅", text_color="green")
            else:
                self.status_label.configure(text="Sistem: OFFLINE ❌", text_color="red")
                # self.log_ui("⚠️ Layanan WhatsApp belum siap. Mencoba lagi...") # Suppress repeat log
                self.after(5000, self.check_service_health) # Retry
        
        threading.Thread(target=_check, daemon=True).start()

    # --- QR CODE LOGIC ---
    def poll_qr_code(self):
        """Periodically checks if QR code is available."""
        def _poll():
            try:
                data = self.controller.get_qr_code()
                if data:
                    status = data.get('status')
                    qr_string = data.get('qr')
                    
                    if status == 'connected':
                        self.status_label.configure(text="WhatsApp: Connected 🔗", text_color="cyan")
                        self.qr_btn.grid_remove()
                        self.logout_btn.grid()
                        
                        if self.qr_window:
                            self.qr_window.destroy()
                            self.qr_window = None
                    
                    elif status == 'scanning' and qr_string:
                        self.status_label.configure(text="WhatsApp: Scan QR 📷", text_color="orange")
                        self.qr_btn.grid()
                        self.logout_btn.grid_remove()
                        
                        if self.qr_window:
                            self.update_qr_image(qr_string)
                            
                    elif status == 'initializing':
                        self.status_label.configure(text="WhatsApp: Init...", text_color="gray")
                        self.qr_btn.grid()
                        self.logout_btn.grid_remove()
                        
            except Exception as e:
                pass
            
            # Poll every 2 seconds
            self.after(2000, self.poll_qr_code)
        
        threading.Thread(target=_poll, daemon=True).start()

    def show_qr_modal(self):
        if self.qr_window is None or not self.qr_window.winfo_exists():
            self.qr_window = ctk.CTkToplevel(self)
            self.qr_window.title("Scan WhatsApp QR")
            self.qr_window.geometry("400x450")
            self.qr_window.attributes("-topmost", True)
            
            label = ctk.CTkLabel(self.qr_window, text="Buka WhatsApp -> Linked Devices -> Link Device\nLalu Scan QR Code dibawah:", font=("Arial", 14))
            label.pack(pady=20)
            
            self.qr_image_label = ctk.CTkLabel(self.qr_window, text="Menunggu QR...", width=250, height=250)
            self.qr_image_label.pack(pady=10)
            
            # Trigger immediate fetch
            threading.Thread(target=self.refresh_qr_display, daemon=True).start()
        else:
            self.qr_window.focus()

    def refresh_qr_display(self):
        try:
            data = self.controller.get_qr_code()
            if not data:
                return

            status = data.get('status')
            qr_string = data.get('qr')

            if qr_string:
                self.update_qr_image(qr_string)
            elif status == 'connected':
                if self.qr_window:
                    for widget in self.qr_window.winfo_children():
                        widget.destroy()
                    ctk.CTkLabel(self.qr_window, text="✅ Terhubung!", font=("Arial", 20), text_color="green").pack(pady=50)
                    self.after(2000, self.qr_window.destroy)
            elif status == 'initializing':
                if self.qr_window:
                     self.qr_image_label.configure(text="Sedang inisialisasi...\nMohon tunggu...", image="")
        except Exception as e:
            self.log_ui(f"Error fetching QR: {e}")

    def update_qr_image(self, qr_data):
        if not self.qr_window or not self.qr_window.winfo_exists():
            return
            
        try:
            # Generate QR Image
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            # Create PIL image
            img = qr.make_image(fill_color="black", back_color="white").get_image()
            
            # Convert to CTkImage
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 250))
            
            self.qr_image_label.configure(image=ctk_img, text="")
        except Exception as e:
            pass # Suppress QR errors in production UI if they are transient

    def logout_whatsapp(self):
        if messagebox.askyesno("Logout", "Apakah anda yakin ingin logout dari WhatsApp?"):
            self.log_ui("🚪 Logging out WhatsApp...")
            def _logout():
                if self.controller.logout_whatsapp():
                    self.log_ui("✅ Logout berhasil. Silakan scan ulang.")
                    self.status_label.configure(text="WhatsApp: Disconnected", text_color="red")
                    # UI update happens in poll_qr_code loop
                else:
                    self.log_ui("❌ Gagal logout.")
            
            threading.Thread(target=_logout, daemon=True).start()


    # --- CORE FEATURES ---
    
    def fetch_groups(self):
        self.log_ui("🔍 Mengambil daftar grup...")
        def _run():
            groups = self.controller.fetch_groups()
            if not groups:
                self.log_ui("⚠️ Tidak ada grup / Gagal koneksi.")
                return
            
            self.log_ui("\n=== DAFTAR GRUP WHATSAPP ===")
            for g in groups:
                self.log_ui(f"📁 {g['name']} | ID: {g['id']}")
            self.log_ui("ℹ️ Copy ID yang berakhiran @g.us ke .env")
            
        threading.Thread(target=_run, daemon=True).start()

    def start_analysis_thread(self, event=None):
        ticker = self.ticker_entry.get().strip()
        if not ticker:
            return
        
        timeframe = self.timeframe_var.get()

        self.toggle_inputs(False)
        self.progress_bar.set(0)
        self.console_textbox.configure(state="normal")
        self.console_textbox.delete("1.0", "end")
        self.console_textbox.configure(state="disabled")
        
        # Clear preview text before starting new analysis
        self.preview_textbox.delete("1.0", "end")

        threading.Thread(target=self.run_analysis_safe, args=(ticker, timeframe), daemon=True).start()

    def run_analysis_safe(self, ticker, timeframe):
        try:
            final_message, chart_path, sentiment_score = self.controller.run_analysis(
                ticker, 
                timeframe=timeframe,
                progress_callback=self.update_progress
            )
            
            self.current_chart_path = chart_path
            self.preview_textbox.insert("end", final_message)
            
            # Update Sentiment UI
            self.update_sentiment_ui(sentiment_score)
            
            self.send_btn.configure(state="normal")
            
            # Update History UI safely in main thread
            self.after(0, self.update_sidebar_lists)
            
        except Exception as e:
            self.log_ui(f"❌ CRITICAL ERROR: {e}")
        finally:
            self.toggle_inputs(True)

    def update_sentiment_ui(self, score):
        # Score is 0-100
        val = score / 100.0
        self.sentiment_bar.set(val)
        self.sentiment_label.configure(text=f"{score}/100")
        
        # Color Logic
        if score >= 75:
            self.sentiment_bar.configure(progress_color="#00ff00") # Green
        elif score >= 60:
            self.sentiment_bar.configure(progress_color="#9acd32") # Light Green
        elif score <= 25:
            self.sentiment_bar.configure(progress_color="#ff0000") # Red
        elif score <= 40:
            self.sentiment_bar.configure(progress_color="#ff4500") # Orange
        else:
            self.sentiment_bar.configure(progress_color="#ffd700") # Gold/Yellow

    def update_progress(self, val):
        self.progress_bar.set(val)

    def toggle_inputs(self, enable):
        state = "normal" if enable else "disabled"
        self.analyze_btn.configure(state=state)
        self.send_btn.configure(state="disabled" if not enable else "normal")

    def send_whatsapp(self):
        message = self.preview_textbox.get("1.0", "end").strip()
        phone = os.getenv("TARGET_PHONE")
        
        if not phone:
            messagebox.showerror("Error", "Set TARGET_PHONE di .env dulu!")
            return
            
        self.log_ui(f"📲 Mengirim ke {phone}...")
        
        def _send():
            try:
                self.controller.send_whatsapp_message(phone, message, self.current_chart_path)
                self.log_ui("✅ Terkirim!")
                messagebox.showinfo("Sukses", "Pesan terkirim!")
            except Exception as e:
                self.log_ui(f"❌ Gagal kirim: {e}")
        
        threading.Thread(target=_send, daemon=True).start()

    def copy_to_clipboard(self):
        text = self.preview_textbox.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.log_ui("📋 Copied.")

    def on_closing(self):
        self.controller.stop_wa_service()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = StockSignalApp()
    app.mainloop()
