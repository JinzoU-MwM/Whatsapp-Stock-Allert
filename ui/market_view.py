import customtkinter as ctk
import os
import threading
from tkinter import messagebox

class MarketView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.current_chart_path = None
        self.setup_ui()

    def setup_ui(self):
        # --- 1. CONTROL CARD (Top) ---
        self.control_card = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.control_card.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=5)
        
        # Grid layout for control card to ensure vertical alignment
        self.control_card.grid_rowconfigure(0, weight=1)
        self.control_card.grid_columnconfigure(0, weight=0) # Ticker
        self.control_card.grid_columnconfigure(1, weight=0) # Save
        self.control_card.grid_columnconfigure(2, weight=1) # Spacer
        self.control_card.grid_columnconfigure(3, weight=0) # Timeframe
        self.control_card.grid_columnconfigure(4, weight=0) # Run

        # Common grid options
        grid_opts = {"row": 0, "pady": 15, "sticky": "ns"}

        # Element 1: Ticker Entry
        self.ticker_entry = ctk.CTkEntry(self.control_card, placeholder_text="TICKER (e.g. BBCA)", width=140, height=40, font=("Arial", 16, "bold"), border_color="gray")
        self.ticker_entry.grid(column=0, padx=(20, 10), **grid_opts)
        self.ticker_entry.bind('<Return>', self.start_analysis_thread)
        self.ticker_entry.bind('<KeyRelease>', lambda e: self.update_favorite_btn_state())

        # Element 2: Save Button
        self.fav_action_btn = ctk.CTkButton(self.control_card, text="☆", width=50, height=40, fg_color="#333", command=self.toggle_favorite)
        self.fav_action_btn.grid(column=1, padx=(0, 10), **grid_opts)

        # Element 3: Timeframe (Segmented)
        self.timeframe_var = ctk.StringVar(value="daily")
        self.tf_seg_btn = ctk.CTkSegmentedButton(self.control_card, values=["Daily", "Weekly", "Monthly"], 
                                                 variable=self.timeframe_var, width=250, height=40, 
                                                 selected_color="#1F6AA5", selected_hover_color="#144870", font=("Arial", 12, "bold"))
        self.tf_seg_btn.grid(column=3, padx=10, **grid_opts)

        # Element 4: Run Analysis Button
        self.analyze_btn = ctk.CTkButton(self.control_card, text="RUN ANALYSIS ⚡", width=200, height=40, 
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       fg_color="#2CC985", hover_color="#25A96E", text_color="black",
                                       command=self.start_analysis_thread)
        self.analyze_btn.grid(column=4, padx=(10, 20), **grid_opts)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.control_card, height=4, progress_color="#2CC985", width=500)
        self.progress_bar.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)
        self.progress_bar.set(0)

        # --- 2. OUTPUT AREA (Frame Switching) ---
        
        # Output Container
        self.output_container = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.output_container.grid(row=1, column=0, sticky="nsew")
        self.output_container.grid_rowconfigure(1, weight=1)
        self.output_container.grid_columnconfigure(0, weight=1)

        # 2a. Tab Selector (Segmented Button - Top Left)
        self.tab_var = ctk.StringVar(value="REPORT PREVIEW")
        self.tab_selector = ctk.CTkSegmentedButton(self.output_container, 
                                                 values=["REPORT PREVIEW", "SYSTEM LOGS", "INFO"],
                                                 command=self.switch_tab,
                                                 variable=self.tab_var,
                                                 selected_color="#2CC985", selected_hover_color="#25A96E", # Emerald Green
                                                 text_color="white", # Default Text
                                                 font=("Arial", 12, "bold"))
        # Hack to change text color of selected button if library supports it, otherwise default contrast applies
        self.tab_selector.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))

        # 2b. Frame: PREVIEW
        self.frame_preview = ctk.CTkFrame(self.output_container, fg_color="transparent")
        self.frame_preview.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.frame_preview.grid_columnconfigure(0, weight=1)
        self.frame_preview.grid_rowconfigure(1, weight=1) # Content expands

        # Row 0: Sentiment Header (Inside Preview)
        self.sent_frame = ctk.CTkFrame(self.frame_preview, fg_color="transparent")
        self.sent_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(self.sent_frame, text="CONFIDENCE SCORE", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w")
        
        score_container = ctk.CTkFrame(self.sent_frame, fg_color="transparent")
        score_container.pack(anchor="w", fill="x", pady=(5, 0))
        
        self.sentiment_val_label = ctk.CTkLabel(score_container, text="--/100", font=("Arial", 32, "bold"), text_color="gray")
        self.sentiment_val_label.pack(side="left", padx=(0, 15))
        
        self.sentiment_bar = ctk.CTkProgressBar(score_container, width=400, height=15, corner_radius=8)
        self.sentiment_bar.pack(side="left", fill="x", expand=True)
        self.sentiment_bar.set(0)

        # Row 1: Content Area
        self.content_area = ctk.CTkFrame(self.frame_preview, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # 1. Empty State Placeholder
        self.placeholder_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.placeholder_frame.grid(row=0, column=0, sticky="nsew")
        
        place_container = ctk.CTkFrame(self.placeholder_frame, fg_color="transparent")
        place_container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(place_container, text="🔍", font=("Arial", 64)).pack(pady=10)
        ctk.CTkLabel(place_container, text="Enter a Stock Ticker to Begin", font=("Arial", 18, "bold"), text_color="gray").pack()

        # 2. Main Textbox
        self.preview_textbox = ctk.CTkTextbox(self.content_area, font=("Consolas", 13), fg_color="#111", text_color="#ddd", corner_radius=5)

        # Row 2: Action Buttons
        self.action_button_frame = ctk.CTkFrame(self.frame_preview, fg_color="transparent", height=50)
        self.action_button_frame.grid(row=2, column=0, sticky="e", padx=10, pady=(5, 10))
        
        self.copy_btn = ctk.CTkButton(self.action_button_frame, text="Copy Text 📋", height=35, width=120, 
                                    fg_color="#444", hover_color="#555", 
                                    command=self.copy_to_clipboard)
        self.copy_btn.pack(side="left", padx=(0, 10))

        self.send_btn = ctk.CTkButton(self.action_button_frame, text="Send WhatsApp 📲", height=35, width=160, 
                                    fg_color="#1F6AA5", hover_color="#144870", font=("Arial", 12, "bold"),
                                    command=self.send_whatsapp, state="disabled")
        self.send_btn.pack(side="left")

        # 2c. Frame: LOGS
        self.frame_logs = ctk.CTkFrame(self.output_container, fg_color="transparent")
        self.frame_logs.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.frame_logs.grid_columnconfigure(0, weight=1)
        self.frame_logs.grid_rowconfigure(0, weight=1)
        
        self.console_textbox = ctk.CTkTextbox(self.frame_logs, font=("Consolas", 11), fg_color="#000", text_color="#0f0", corner_radius=5)
        self.console_textbox.grid(row=0, column=0, sticky="nsew")
        self.console_textbox.configure(state="disabled")

        # 2d. Frame: INFO
        self.frame_info = ctk.CTkFrame(self.output_container, fg_color="transparent")
        self.frame_info.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        ctk.CTkLabel(self.frame_info, text="Stock Intelligence v2.0", font=("Arial", 20, "bold")).pack(pady=20)
        self.group_btn = ctk.CTkButton(self.frame_info, text="Scan WhatsApp Group IDs", command=self.fetch_groups)
        self.group_btn.pack()

        # Initialize View State
        self.switch_tab("REPORT PREVIEW")

    # --- LOGIC ---

    def switch_tab(self, value):
        # Hide all frames
        self.frame_preview.grid_remove()
        self.frame_logs.grid_remove()
        self.frame_info.grid_remove()
        
        # Show selected
        if value == "REPORT PREVIEW":
            self.frame_preview.grid()
        elif value == "SYSTEM LOGS":
            self.frame_logs.grid()
        elif value == "INFO":
            self.frame_info.grid()

    def log_message(self, message):
        """Called by Controller to log text"""
        try:
            self.console_textbox.configure(state="normal")
            self.console_textbox.insert("end", f"> {message}\n")
            self.console_textbox.see("end")
            self.console_textbox.configure(state="disabled")
        except:
            pass # Widget might be destroyed on exit

    def start_analysis_thread(self, event=None):
        ticker = self.ticker_entry.get().strip()
        if not ticker:
            return
        
        timeframe = self.timeframe_var.get().lower()

        self.toggle_inputs(False)
        self.progress_bar.set(0)
        
        # Auto-switch to logs
        self.tab_selector.set("SYSTEM LOGS")
        self.switch_tab("SYSTEM LOGS")
        
        self.console_textbox.configure(state="normal")
        self.console_textbox.delete("1.0", "end")
        self.console_textbox.configure(state="disabled")
        
        # Reset Preview UI
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.grid_forget()
        self.placeholder_frame.grid(row=0, column=0, sticky="nsew")
        
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
            
            # Auto-switch back to preview
            self.tab_selector.set("REPORT PREVIEW")
            self.switch_tab("REPORT PREVIEW")
            
            self.update_sentiment_ui(sentiment_score)
            self.send_btn.configure(state="normal")
            
            # Request Sidebar Update
            if hasattr(self.master.master, "sidebar"):
                 self.master.master.sidebar.update_lists()
            
        except Exception as e:
            self.log_message(f"❌ CRITICAL ERROR: {e}")
            # Ensure we stay on logs if error
            self.tab_selector.set("SYSTEM LOGS")
            self.switch_tab("SYSTEM LOGS")
        finally:
            self.toggle_inputs(True)

    def update_sentiment_ui(self, score):
        val = score / 100.0
        self.sentiment_bar.set(val)
        self.sentiment_val_label.configure(text=f"{score}/100")
        
        if score >= 75: color = "#00ff00"
        elif score >= 60: color = "#9acd32"
        elif score <= 25: color = "#ff0000"
        elif score <= 40: color = "#ff4500"
        else: color = "#ffd700"
        
        self.sentiment_bar.configure(progress_color=color)
        self.sentiment_val_label.configure(text_color=color)

    def update_progress(self, val):
        self.progress_bar.set(val)

    def toggle_inputs(self, enable):
        state = "normal" if enable else "disabled"
        self.analyze_btn.configure(state=state)
        self.send_btn.configure(state="disabled" if not enable else "normal")

    def copy_to_clipboard(self):
        text = self.preview_textbox.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.log_message("📋 Text copied to clipboard.")

    def send_whatsapp(self):
        message = self.preview_textbox.get("1.0", "end").strip()
        phone = os.getenv("TARGET_PHONE")
        
        if not phone:
            messagebox.showerror("Error", "Set TARGET_PHONE di .env dulu!")
            return
        
        self.log_message(f"📲 Sending to {phone}...")
        
        def _send():
            try:
                self.controller.send_whatsapp_message(phone, message, self.current_chart_path)
                self.log_message("✅ Sent!")
                messagebox.showinfo("Success", "Message sent to WhatsApp!")
            except Exception as e:
                self.log_message(f"❌ Failed to send: {e}")
        
        threading.Thread(target=_send, daemon=True).start()

    def fetch_groups(self):
        self.log_message("🔍 Fetching WhatsApp Groups...")
        def _run():
            groups = self.controller.fetch_groups()
            if not groups:
                self.log_message("⚠️ No groups found or connection failed.")
                return
            
            self.log_message("\n=== WHATSAPP GROUPS ===")
            for g in groups:
                self.log_message(f"📁 {g['name']} | ID: {g['id']}")
            self.log_message("ℹ️ Copy Group ID ending in @g.us to .env")
            
        threading.Thread(target=_run, daemon=True).start()

    # Favorites Logic
    def load_ticker(self, ticker):
        self.ticker_entry.delete(0, "end")
        self.ticker_entry.insert(0, ticker)
        self.update_favorite_btn_state()

    def toggle_favorite(self):
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker: return
        
        if self.controller.is_favorite(ticker):
            self.controller.remove_favorite(ticker)
        else:
            self.controller.add_favorite(ticker)
            
        self.update_favorite_btn_state()
        # Update sidebar
        if hasattr(self.master.master, "sidebar"):
             self.master.master.sidebar.update_lists()

    def update_favorite_btn_state(self):
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            self.fav_action_btn.configure(state="disabled", text="★")
            return
            
        self.fav_action_btn.configure(state="normal")
        if self.controller.is_favorite(ticker):
            self.fav_action_btn.configure(text="★ Saved", fg_color="#D4AF37", text_color="black", hover_color="#C5A028")
        else:
            self.fav_action_btn.configure(text="☆ Save", fg_color="#333", text_color="white", hover_color="#444")
