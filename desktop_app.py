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

        self.title("StockSignal Intelligence (Bloomberg Edition)")
        self.geometry("1100x800")

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
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1) # Spacer push to bottom

        # Logo / Title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="STOCK\nINTELLIGENCE", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        # Status
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="SYSTEM: INIT...", text_color="gray", font=ctk.CTkFont(size=11))
        self.status_label.grid(row=1, column=0, padx=20, pady=5)
        
        # QR Button
        self.qr_btn = ctk.CTkButton(self.sidebar_frame, text="LINK WHATSAPP", command=self.show_qr_modal, fg_color="#333", border_width=1, border_color="gray")
        self.qr_btn.grid(row=2, column=0, padx=20, pady=10)
        
        # Favorites Section
        self.fav_label = ctk.CTkLabel(self.sidebar_frame, text="FAVORITE TICKERS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#aaa")
        self.fav_label.grid(row=3, column=0, padx=20, pady=(30, 5), sticky="w")

        self.fav_frame = ctk.CTkScrollableFrame(self.sidebar_frame, width=180, height=250, fg_color="transparent")
        self.fav_frame.grid(row=4, column=0, padx=10, pady=5)
        
        # History Section
        self.hist_label = ctk.CTkLabel(self.sidebar_frame, text="RECENT HISTORY", font=ctk.CTkFont(size=12, weight="bold"), text_color="#aaa")
        self.hist_label.grid(row=5, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.hist_frame = ctk.CTkScrollableFrame(self.sidebar_frame, width=180, height=150, fg_color="transparent")
        self.hist_frame.grid(row=6, column=0, padx=10, pady=5)

        # Logout Button (Bottom)
        self.logout_btn = ctk.CTkButton(self.sidebar_frame, text="DISCONNECT WA", command=self.logout_whatsapp, fg_color="#330000", hover_color="#550000", border_width=1, border_color="#550000")
        self.logout_btn.grid(row=8, column=0, padx=20, pady=20)
        self.logout_btn.grid_remove() # Hidden initially

    def update_sidebar_lists(self):
        # Refresh Favorites
        for widget in self.fav_frame.winfo_children():
            widget.destroy()
            
        favorites = self.controller.get_favorites()
        if not favorites:
            ctk.CTkLabel(self.fav_frame, text="No Favorites", text_color="gray", font=("Arial", 10)).pack()
        else:
            for ticker in favorites:
                # Row frame
                row = ctk.CTkFrame(self.fav_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                # Ticker Button (Load) - Style: Menu Item
                btn = ctk.CTkButton(row, text=f"★ {ticker}", width=120, height=28, anchor="w", fg_color="transparent", hover_color="#333",
                                  font=ctk.CTkFont(size=12),
                                  command=lambda t=ticker: self.load_ticker(t))
                btn.pack(side="left", padx=2)
                
                # Delete Button
                del_btn = ctk.CTkButton(row, text="×", width=25, height=25, fg_color="transparent", hover_color="#500", text_color="gray",
                                      command=lambda t=ticker: self.remove_favorite(t))
                del_btn.pack(side="right", padx=2)

        # Refresh History
        for widget in self.hist_frame.winfo_children():
            widget.destroy()
            
        history = self.controller.get_history(limit=15)
        if not history:
            ctk.CTkLabel(self.hist_frame, text="No History", text_color="gray", font=("Arial", 10)).pack()
        else:
            for ticker in history:
                btn = ctk.CTkButton(self.hist_frame, text=f"• {ticker}", height=24, anchor="w", fg_color="transparent", hover_color="#333",
                                  text_color="#ccc", font=ctk.CTkFont(size=11),
                                  command=lambda t=ticker: self.load_ticker(t))
                btn.pack(fill="x", pady=1)

    def load_ticker(self, ticker):
        self.ticker_entry.delete(0, "end")
        self.ticker_entry.insert(0, ticker)
        self.update_favorite_btn_state(ticker)

    def add_favorite(self):
        ticker = self.ticker_entry.get().strip().upper()
        if ticker:
            if self.controller.add_favorite(ticker):
                self.update_sidebar_lists()
                self.update_favorite_btn_state(ticker)

    def remove_favorite(self, ticker):
        self.controller.remove_favorite(ticker)
        self.update_sidebar_lists()
        current = self.ticker_entry.get().strip().upper()
        if current == ticker:
            self.update_favorite_btn_state(current)

    def update_favorite_btn_state(self, ticker):
        if not ticker:
            self.fav_action_btn.configure(state="disabled", text="★")
            return
            
        self.fav_action_btn.configure(state="normal")
        if self.controller.is_favorite(ticker):
            self.fav_action_btn.configure(text="★ Saved", fg_color="#D4AF37", text_color="black", hover_color="#C5A028", command=lambda: self.remove_favorite(ticker))
        else:
            self.fav_action_btn.configure(text="☆ Save", fg_color="#333", text_color="white", hover_color="#444", command=self.add_favorite)

    def setup_main_area(self):
        # Main Layout: 2 Rows. Top = Control Card, Bottom = Tabview Output
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1) # Bottom expands
        self.main_frame.grid_columnconfigure(0, weight=1)

        # --- 1. CONTROL CARD (Top) ---
        self.control_card = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.control_card.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=15)
        
        # Grid layout for control card to ensure vertical alignment
        self.control_card.grid_columnconfigure(0, weight=0) # Ticker
        self.control_card.grid_columnconfigure(1, weight=0) # Save
        self.control_card.grid_columnconfigure(2, weight=1) # Spacer
        self.control_card.grid_columnconfigure(3, weight=0) # Timeframe
        self.control_card.grid_columnconfigure(4, weight=0) # Run

        # Element 1: Ticker Entry
        self.ticker_entry = ctk.CTkEntry(self.control_card, placeholder_text="TICKER (e.g. BBCA)", width=140, height=40, font=("Arial", 16, "bold"), border_color="gray")
        self.ticker_entry.grid(row=0, column=0, padx=(20, 10), pady=10)
        self.ticker_entry.bind('<Return>', self.start_analysis_thread)
        self.ticker_entry.bind('<KeyRelease>', lambda e: self.update_favorite_btn_state(self.ticker_entry.get().strip().upper()))

        # Element 2: Save Button
        self.fav_action_btn = ctk.CTkButton(self.control_card, text="☆", width=50, height=40, fg_color="#333", command=self.add_favorite)
        self.fav_action_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        # Element 3: Timeframe (Segmented)
        self.timeframe_var = ctk.StringVar(value="daily")
        self.tf_seg_btn = ctk.CTkSegmentedButton(self.control_card, values=["Daily", "Weekly", "Monthly"], 
                                                 variable=self.timeframe_var, width=250, height=40, 
                                                 selected_color="#1F6AA5", selected_hover_color="#144870", font=("Arial", 12, "bold"))
        self.tf_seg_btn.grid(row=0, column=3, padx=10, pady=10)

        # Element 4: Run Analysis Button (Accent Color, Large)
        self.analyze_btn = ctk.CTkButton(self.control_card, text="RUN ANALYSIS ⚡", width=200, height=40, 
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       fg_color="#2CC985", hover_color="#25A96E", text_color="black", # Emerald Green
                                       command=self.start_analysis_thread)
        self.analyze_btn.grid(row=0, column=4, padx=(10, 20), pady=10)

        # Progress Bar (Attached to bottom of card)
        self.progress_bar = ctk.CTkProgressBar(self.control_card, height=4, progress_color="#2CC985", width=500)
        self.progress_bar.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)
        self.progress_bar.set(0)

        # --- 2. OUTPUT AREA (Tabs) ---
        self.output_tabview = ctk.CTkTabview(self.main_frame, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333", segmented_button_selected_color="#1F6AA5")
        self.output_tabview.grid(row=1, column=0, sticky="nsew")
        
        # Create Tabs
        self.tab_preview = self.output_tabview.add("📊 REPORT PREVIEW")
        self.tab_logs = self.output_tabview.add("🤖 SYSTEM LOGS")
        self.tab_info = self.output_tabview.add("ℹ️ INFO")

        # --- TAB 1: PREVIEW LAYOUT ---
        self.tab_preview.grid_columnconfigure(0, weight=1)
        self.tab_preview.grid_rowconfigure(1, weight=1) # Textbox area
        
        # Row 0: Sentiment Header (Big UI)
        self.sent_frame = ctk.CTkFrame(self.tab_preview, fg_color="transparent")
        self.sent_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(self.sent_frame, text="CONFIDENCE SCORE", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w")
        
        # Score Container
        score_container = ctk.CTkFrame(self.sent_frame, fg_color="transparent")
        score_container.pack(anchor="w", fill="x", pady=(5, 0))
        
        self.sentiment_val_label = ctk.CTkLabel(score_container, text="--/100", font=("Arial", 32, "bold"), text_color="gray")
        self.sentiment_val_label.pack(side="left", padx=(0, 15))
        
        self.sentiment_bar = ctk.CTkProgressBar(score_container, width=400, height=15, corner_radius=8)
        self.sentiment_bar.pack(side="left", fill="x", expand=True)
        self.sentiment_bar.set(0)

        # Row 1: Content Area (Placeholder + Textbox)
        self.content_area = ctk.CTkFrame(self.tab_preview, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # 1. Empty State Placeholder
        self.placeholder_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.placeholder_frame.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.placeholder_frame, text="🔍", font=("Arial", 48)).pack(pady=(80, 10))
        ctk.CTkLabel(self.placeholder_frame, text="Enter a Ticker to Begin Analysis", font=("Arial", 16, "bold"), text_color="gray").pack()

        # 2. Main Textbox (Hidden Initially)
        self.preview_textbox = ctk.CTkTextbox(self.content_area, font=("Consolas", 13), fg_color="#111", text_color="#ddd", corner_radius=5)
        # We don't grid it yet, logic will switch it

        # Row 2: Action Buttons (Bottom Right)
        self.action_button_frame = ctk.CTkFrame(self.tab_preview, fg_color="transparent")
        self.action_button_frame.grid(row=2, column=0, sticky="e", padx=20, pady=15)

        self.copy_btn = ctk.CTkButton(self.action_button_frame, text="Copy Text 📋", height=35, width=120, 
                                    fg_color="#444", hover_color="#555", 
                                    command=self.copy_to_clipboard)
        self.copy_btn.pack(side="left", padx=(0, 10))

        self.send_btn = ctk.CTkButton(self.action_button_frame, text="Send WhatsApp 📲", height=35, width=160, 
                                    fg_color="#1F6AA5", hover_color="#144870", font=("Arial", 12, "bold"),
                                    command=self.send_whatsapp, state="disabled")
        self.send_btn.pack(side="left")

        # --- TAB 2: LOGS ---
        self.tab_logs.grid_columnconfigure(0, weight=1)
        self.tab_logs.grid_rowconfigure(0, weight=1)
        
        self.console_textbox = ctk.CTkTextbox(self.tab_logs, font=("Consolas", 11), fg_color="#000", text_color="#0f0", corner_radius=5)
        self.console_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.console_textbox.configure(state="disabled")

        # --- TAB 3: INFO ---
        ctk.CTkLabel(self.tab_info, text="Stock Intelligence v2.0", font=("Arial", 20, "bold")).pack(pady=20)
        self.group_btn = ctk.CTkButton(self.tab_info, text="Scan WhatsApp Group IDs", command=self.fetch_groups)
        self.group_btn.pack()

    # --- LOGIC & BINDINGS ---

    def log_ui(self, message):
        """Callback for Controller to log to UI"""
        self.console_textbox.configure(state="normal")
        self.console_textbox.insert("end", f"> {message}\n")
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
                self.status_label.configure(text="SYSTEM: ONLINE ✅", text_color="#2CC985")
            else:
                self.status_label.configure(text="SYSTEM: OFFLINE ❌", text_color="red")
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
                        self.status_label.configure(text="WA: CONNECTED 🔗", text_color="#2CC985")
                        self.qr_btn.grid_remove()
                        self.logout_btn.grid()
                        
                        if self.qr_window:
                            self.qr_window.destroy()
                            self.qr_window = None
                    
                    elif status == 'scanning' and qr_string:
                        self.status_label.configure(text="WA: SCAN QR 📷", text_color="orange")
                        self.qr_btn.grid()
                        self.logout_btn.grid_remove()
                        
                        if self.qr_window:
                            self.update_qr_image(qr_string)
                            
                    elif status == 'initializing':
                        self.status_label.configure(text="WA: INIT...", text_color="gray")
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
            
            label = ctk.CTkLabel(self.qr_window, text="Buka WhatsApp -> Linked Devices\nLalu Scan QR Code:", font=("Arial", 14))
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
        if messagebox.askyesno("Logout", "Putuskan koneksi WhatsApp?"):
            self.log_ui("🚪 Disconnecting WhatsApp...")
            def _logout():
                if self.controller.logout_whatsapp():
                    self.log_ui("✅ Disconnected.")
                    self.status_label.configure(text="WA: DISCONNECTED", text_color="red")
                else:
                    self.log_ui("❌ Failed to disconnect.")
            
            threading.Thread(target=_logout, daemon=True).start()


    # --- CORE FEATURES ---
    
    def fetch_groups(self):
        self.log_ui("🔍 Fetching WhatsApp Groups...")
        def _run():
            groups = self.controller.fetch_groups()
            if not groups:
                self.log_ui("⚠️ No groups found or connection failed.")
                return
            
            self.log_ui("\n=== WHATSAPP GROUPS ===")
            for g in groups:
                self.log_ui(f"📁 {g['name']} | ID: {g['id']}")
            self.log_ui("ℹ️ Copy Group ID ending in @g.us to .env")
            
        threading.Thread(target=_run, daemon=True).start()

    def start_analysis_thread(self, event=None):
        ticker = self.ticker_entry.get().strip()
        if not ticker:
            return
        
        timeframe = self.timeframe_var.get().lower() # Convert segmented val to lowercase

        self.toggle_inputs(False)
        self.progress_bar.set(0)
        self.output_tabview.set("🤖 SYSTEM LOGS") # Switch to logs during process
        self.console_textbox.configure(state="normal")
        self.console_textbox.delete("1.0", "end")
        self.console_textbox.configure(state="disabled")
        
        # Reset Preview UI
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.grid_forget() # Hide textbox
        self.placeholder_frame.grid(row=0, column=0, sticky="nsew") # Show placeholder (or loading spinner if we had one)
        
        # Reset Sentiment
        self.sentiment_bar.set(0)
        self.sentiment_val_label.configure(text="--/100", text_color="gray")

        threading.Thread(target=self.run_analysis_safe, args=(ticker, timeframe), daemon=True).start()

    def run_analysis_safe(self, ticker, timeframe):
        try:
            final_message, chart_path, sentiment_score = self.controller.run_analysis(
                ticker, 
                timeframe=timeframe,
                progress_callback=self.update_progress
            )
            
            self.current_chart_path = chart_path
            
            # Switch UI to Result Mode
            self.placeholder_frame.grid_forget()
            self.preview_textbox.grid(row=0, column=0, sticky="nsew")
            
            self.preview_textbox.insert("end", final_message)
            
            # Switch to Preview Tab
            self.output_tabview.set("📊 REPORT PREVIEW")
            
            # Update Sentiment UI
            self.update_sentiment_ui(sentiment_score)
            
            self.send_btn.configure(state="normal")
            
            # Update History UI safely in main thread
            self.after(0, self.update_sidebar_lists)
            
        except Exception as e:
            self.log_ui(f"❌ CRITICAL ERROR: {e}")
            self.output_tabview.set("🤖 SYSTEM LOGS")
        finally:
            self.toggle_inputs(True)

    def update_sentiment_ui(self, score):
        # Score is 0-100
        val = score / 100.0
        self.sentiment_bar.set(val)
        self.sentiment_val_label.configure(text=f"{score}/100")
        
        # Color Logic
        if score >= 75:
            self.sentiment_bar.configure(progress_color="#00ff00") # Green
            self.sentiment_val_label.configure(text_color="#00ff00")
        elif score >= 60:
            self.sentiment_bar.configure(progress_color="#9acd32") # Light Green
            self.sentiment_val_label.configure(text_color="#9acd32")
        elif score <= 25:
            self.sentiment_bar.configure(progress_color="#ff0000") # Red
            self.sentiment_val_label.configure(text_color="#ff0000")
        elif score <= 40:
            self.sentiment_bar.configure(progress_color="#ff4500") # Orange
            self.sentiment_val_label.configure(text_color="#ff4500")
        else:
            self.sentiment_bar.configure(progress_color="#ffd700") # Gold/Yellow
            self.sentiment_val_label.configure(text_color="#ffd700")

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
            
        self.log_ui(f"📲 Sending to {phone}...")
        
        def _send():
            try:
                self.controller.send_whatsapp_message(phone, message, self.current_chart_path)
                self.log_ui("✅ Sent!")
                messagebox.showinfo("Success", "Message sent to WhatsApp!")
            except Exception as e:
                self.log_ui(f"❌ Failed to send: {e}")
        
        threading.Thread(target=_send, daemon=True).start()

    def copy_to_clipboard(self):
        text = self.preview_textbox.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.log_ui("📋 Text copied to clipboard.")

    def on_closing(self):
        self.controller.stop_wa_service()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = StockSignalApp()
    app.mainloop()
