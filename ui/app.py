import customtkinter as ctk
from tkinter import messagebox
import threading
import sys
import os
import time
import qrcode
from PIL import Image

# View Modules
from ui.sidebar import Sidebar
from ui.market_view import MarketView
from ui.portfolio_view import PortfolioView
from ui.settings_view import SettingsView

# Import Controller
# Assuming this file is run from root via desktop_app.py which sets sys.path
try:
    from app_controller import StockAppController
except ImportError:
    # Fallback if run directly from ui folder (debugging)
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stock-intelligence'))
    from app_controller import StockAppController

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StockSignalApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("StockSignal Intelligence (Bloomberg Edition)")
        self.geometry("1100x800")

        # Initialize Controller
        # We pass a lambda to route logs to the MarketView (since that's where the console is)
        self.controller = StockAppController(log_callback=self.log_router)
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # UI Components
        self.sidebar = Sidebar(self, self.controller, self)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")

        # Main Container
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Views
        self.market_view = MarketView(self.main_container, self.controller)
        self.portfolio_view = PortfolioView(self.main_container, self.controller)
        self.settings_view = SettingsView(self.main_container, self.controller)
        
        # Default View
        self.show_market_view()
        
        # State
        self.qr_window = None
        self.qr_image_label = None
        
        # Startup Checks
        self.check_api_keys()
        self.controller.start_wa_service()
        self.check_service_health()
        
        # Start QR Polling
        self.after(3000, self.poll_qr_code)
        
        # Cleanup on exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log_router(self, message):
        """Routes logs from controller to the active view (MarketView console)"""
        if self.market_view:
            self.market_view.log_message(message)

    # --- VIEW NAVIGATION ---
    def show_market_view(self):
        self.sidebar.btn_nav_market.configure(fg_color="#1F6AA5", text_color="white")
        self.sidebar.btn_nav_portfolio.configure(fg_color="transparent", text_color="gray")
        self.sidebar.btn_nav_settings.configure(fg_color="transparent", text_color="gray")
        
        self.portfolio_view.grid_forget()
        self.settings_view.grid_forget()
        self.market_view.grid(row=0, column=0, sticky="nsew")

    def show_portfolio_view(self):
        self.sidebar.btn_nav_market.configure(fg_color="transparent", text_color="gray")
        self.sidebar.btn_nav_portfolio.configure(fg_color="#1F6AA5", text_color="white")
        self.sidebar.btn_nav_settings.configure(fg_color="transparent", text_color="gray")
        
        self.market_view.grid_forget()
        self.settings_view.grid_forget()
        self.portfolio_view.grid(row=0, column=0, sticky="nsew")
        
        self.portfolio_view.refresh_portfolio_table()

    def show_settings_view(self):
        self.sidebar.btn_nav_market.configure(fg_color="transparent", text_color="gray")
        self.sidebar.btn_nav_portfolio.configure(fg_color="transparent", text_color="gray")
        self.sidebar.btn_nav_settings.configure(fg_color="#1F6AA5", text_color="white")
        
        self.market_view.grid_forget()
        self.portfolio_view.grid_forget()
        self.settings_view.load_data() # Refresh data
        self.settings_view.grid(row=0, column=0, sticky="nsew")

    def load_ticker(self, ticker):
        self.show_market_view()
        self.market_view.load_ticker(ticker)

    # --- SYSTEM CHECKS ---
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
                self.sidebar.update_status("SYSTEM: ONLINE ✅", "#2CC985")
            else:
                self.sidebar.update_status("SYSTEM: OFFLINE ❌", "red")
                self.after(5000, self.check_service_health) # Retry
        
        threading.Thread(target=_check, daemon=True).start()

    # --- QR & WHATSAPP ---
    def poll_qr_code(self):
        def _poll():
            try:
                data = self.controller.get_qr_code()
                if data:
                    status = data.get('status')
                    qr_string = data.get('qr')
                    
                    if status == 'connected':
                        self.sidebar.update_status("WA: CONNECTED 🔗", "#2CC985")
                        self.sidebar.show_qr_btn(False)
                        if self.qr_window:
                            self.qr_window.destroy()
                            self.qr_window = None
                    
                    elif status == 'scanning' and qr_string:
                        self.sidebar.update_status("WA: SCAN QR 📷", "orange")
                        self.sidebar.show_qr_btn(True)
                        if self.qr_window:
                            self.update_qr_image(qr_string)
                            
                    elif status == 'initializing':
                        self.sidebar.update_status("WA: INIT...", "gray")
                        self.sidebar.show_qr_btn(True)
                        
            except Exception:
                pass
            self.after(2000, self.poll_qr_code)
        
        threading.Thread(target=_poll, daemon=True).start()

    def show_qr_modal(self):
        if self.qr_window is None or not self.qr_window.winfo_exists():
            self.qr_window = ctk.CTkToplevel(self)
            self.qr_window.title("Scan WhatsApp QR")
            self.qr_window.geometry("400x450")
            self.qr_window.attributes("-topmost", True)
            
            label = ctk.CTkLabel(self.qr_window, text="Buka WhatsApp -> Linked Devices\nLalu Scan QR Code:", font=("Arial", 14))
            label.pack(pady=20)
            
            self.qr_image_label = ctk.CTkLabel(self.qr_window, text="Menunggu QR...", width=250, height=250)
            self.qr_image_label.pack(pady=10)
            
            threading.Thread(target=self.refresh_qr_display, daemon=True).start()
        else:
            self.qr_window.focus()

    def refresh_qr_display(self):
        try:
            data = self.controller.get_qr_code()
            if not data: return
            
            status = data.get('status')
            qr_string = data.get('qr')

            if qr_string:
                self.update_qr_image(qr_string)
            elif status == 'connected':
                if self.qr_window:
                    for widget in self.qr_window.winfo_children(): widget.destroy()
                    ctk.CTkLabel(self.qr_window, text="✅ Terhubung!", font=("Arial", 20), text_color="green").pack(pady=50)
                    self.after(2000, self.qr_window.destroy)
            elif status == 'initializing':
                if self.qr_window:
                     self.qr_image_label.configure(text="Sedang inisialisasi...\nMohon tunggu...", image="")
        except Exception as e:
            self.log_router(f"Error fetching QR: {e}")

    def update_qr_image(self, qr_data):
        if not self.qr_window or not self.qr_window.winfo_exists(): return
        try:
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").get_image()
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 250))
            self.qr_image_label.configure(image=ctk_img, text="")
        except: pass

    def logout_whatsapp(self):
        if messagebox.askyesno("Logout", "Putuskan koneksi WhatsApp?"):
            self.log_router("🚪 Disconnecting WhatsApp...")
            def _logout():
                if self.controller.logout_whatsapp():
                    self.log_router("✅ Disconnected.")
                    self.sidebar.update_status("WA: DISCONNECTED", "red")
                else:
                    self.log_router("❌ Failed to disconnect.")
            threading.Thread(target=_logout, daemon=True).start()

    def on_closing(self):
        self.controller.stop_wa_service()
        self.destroy()
        sys.exit(0)
