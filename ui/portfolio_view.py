import customtkinter as ctk
import threading
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PortfolioView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.setup_ui()

    def setup_ui(self):
        # 1. Input Card
        self.port_input = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.port_input.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=10)
        
        ctk.CTkLabel(self.port_input, text="MANAGE PORTFOLIO", font=("Arial", 14, "bold"), text_color="#2CC985").pack(pady=5)
        
        input_row = ctk.CTkFrame(self.port_input, fg_color="transparent")
        input_row.pack(pady=5)
        
        self.port_ticker = ctk.CTkEntry(input_row, placeholder_text="Ticker (e.g. BBCA)", width=120)
        self.port_ticker.pack(side="left", padx=5)
        
        self.port_price = ctk.CTkEntry(input_row, placeholder_text="Avg Price (Rp)", width=120)
        self.port_price.pack(side="left", padx=5)
        
        self.port_lots = ctk.CTkEntry(input_row, placeholder_text="Lots (Qty)", width=80)
        self.port_lots.pack(side="left", padx=5)
        
        ctk.CTkButton(input_row, text="+ BUY / AVG", width=120, fg_color="#1F6AA5", command=self.add_portfolio_entry).pack(side="left", padx=10)

        # 2. Main Content Area (Split Table and Chart)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=3) # Table takes 3 parts
        self.content_frame.grid_columnconfigure(1, weight=2) # Chart takes 2 parts
        self.content_frame.grid_rowconfigure(0, weight=1)

        # 2a. Table Area (Left)
        self.table_container = ctk.CTkFrame(self.content_frame, corner_radius=10, fg_color="#111", border_width=1, border_color="#333")
        self.table_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.table_container.grid_columnconfigure(0, weight=1)
        self.table_container.grid_rowconfigure(1, weight=1)
        
        # Header Row
        header_frame = ctk.CTkFrame(self.table_container, fg_color="#222", height=30)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)
        
        headers = ["TICKER", "AVG", "LOTS", "PRICE", "VAL (M)", "P/L %", "ACT"]
        for idx, h in enumerate(headers):
            ctk.CTkLabel(header_frame, text=h, font=("Arial", 10, "bold"), text_color="gray").grid(row=0, column=idx, pady=5)

        # Scrollable Rows
        self.table_scroll = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.table_scroll.grid(row=1, column=0, sticky="nsew")
        self.table_scroll.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)

        # 2b. Chart Area (Right)
        self.chart_frame = ctk.CTkFrame(self.content_frame, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.chart_frame.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(self.chart_frame, text="ALLOCATION", font=("Arial", 12, "bold"), text_color="gray").pack(pady=10)
        self.canvas_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 3. Footer Summary
        self.footer_frame = ctk.CTkFrame(self, height=60, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.footer_frame.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        
        self.total_val_label = ctk.CTkLabel(self.footer_frame, text="Equity: Rp 0", font=("Arial", 16, "bold"))
        self.total_val_label.pack(side="left", padx=20, pady=15)
        
        self.total_pl_label = ctk.CTkLabel(self.footer_frame, text="P/L: Rp 0 (0%)", font=("Arial", 16, "bold"))
        self.total_pl_label.pack(side="left", padx=20, pady=15)
        
        ctk.CTkButton(self.footer_frame, text="REFRESH PRICES ⚡", fg_color="#2CC985", text_color="black", font=("Arial", 12, "bold"), command=self.refresh_portfolio_table).pack(side="right", padx=20)

    def add_portfolio_entry(self):
        t = self.port_ticker.get().strip().upper()
        p = self.port_price.get().strip()
        l = self.port_lots.get().strip()
        
        if not t or not p or not l:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        try:
            p_val = float(p)
            l_val = int(l)
            if self.controller.add_portfolio_item(t, p_val, l_val):
                self.port_ticker.delete(0, "end")
                self.port_price.delete(0, "end")
                self.port_lots.delete(0, "end")
                self.refresh_portfolio_table()
        except ValueError:
            messagebox.showerror("Error", "Price must be number, Lots must be integer")

    def delete_portfolio_entry(self, ticker):
        if messagebox.askyesno("Confirm", f"Remove {ticker} from portfolio?"):
            self.controller.remove_portfolio_item(ticker)
            self.refresh_portfolio_table()

    def refresh_portfolio_table(self):
        # Clear existing rows
        for widget in self.table_scroll.winfo_children():
            widget.destroy()
        
        # Fetch Data (Threaded)
        def _fetch():
            data = self.controller.get_portfolio_summary()
            self.after(0, lambda: self._populate_table(data))
            
        threading.Thread(target=_fetch, daemon=True).start()

    def _populate_table(self, data):
        total_equity = 0
        total_pl_val = 0
        total_invest = 0
        
        chart_labels = []
        chart_sizes = []
        
        for idx, item in enumerate(data):
            # Data
            tick = item['ticker']
            avg = item['avg_price']
            lots = item['lots']
            curr = item.get('current_price', 0)
            mkt_val = item.get('market_value', 0)
            pl_pct = item.get('pl_pct', 0)
            pl_val = item.get('pl_value', 0)
            
            # Totals
            total_equity += mkt_val
            total_pl_val += pl_val
            total_invest += (avg * lots * 100)
            
            # Chart Data
            if mkt_val > 0:
                chart_labels.append(tick)
                chart_sizes.append(mkt_val)
            
            # Color
            pl_color = "#00ff00" if pl_pct >= 0 else "#ff0000"
            
            # Row Widgets (Inside Scrollable)
            ctk.CTkLabel(self.table_scroll, text=tick, font=("Arial", 12, "bold")).grid(row=idx, column=0, pady=5)
            ctk.CTkLabel(self.table_scroll, text=f"{avg:,.0f}").grid(row=idx, column=1, pady=5)
            ctk.CTkLabel(self.table_scroll, text=f"{lots}").grid(row=idx, column=2, pady=5)
            ctk.CTkLabel(self.table_scroll, text=f"{curr:,.0f}").grid(row=idx, column=3, pady=5)
            # Shorten Value display (e.g. 15.5M)
            val_display = f"{mkt_val/1_000_000:.1f}M" if mkt_val > 1_000_000 else f"{mkt_val:,.0f}"
            ctk.CTkLabel(self.table_scroll, text=val_display).grid(row=idx, column=4, pady=5)
            ctk.CTkLabel(self.table_scroll, text=f"{pl_pct:+.1f}%", text_color=pl_color).grid(row=idx, column=5, pady=5)
            
            ctk.CTkButton(self.table_scroll, text="✕", width=30, height=20, fg_color="#500", command=lambda t=tick: self.delete_portfolio_entry(t)).grid(row=idx, column=6, pady=5)

        # Update Footer
        total_pl_pct = (total_pl_val / total_invest * 100) if total_invest > 0 else 0
        pl_color = "#00ff00" if total_pl_val >= 0 else "#ff0000"
        
        self.total_val_label.configure(text=f"Equity: Rp {total_equity:,.0f}")
        self.total_pl_label.configure(text=f"P/L: Rp {total_pl_val:,.0f} ({total_pl_pct:+.2f}%)", text_color=pl_color)
        
        # Render Chart
        self._render_pie_chart(chart_labels, chart_sizes)

    def _render_pie_chart(self, labels, sizes):
        # Clear previous chart
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
            
        if not sizes:
            return

        # Create Figure (Dark Theme)
        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        fig.patch.set_facecolor('#1a1a1a') # Background
        ax.set_facecolor('#1a1a1a')
        
        # Colors (Cyberpunk Palette)
        colors = ['#2CC985', '#1F6AA5', '#D4AF37', '#FF4500', '#9ACD32', '#00FFFF']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                          startangle=90, colors=colors[:len(labels)],
                                          textprops=dict(color="white"))
        
        plt.setp(autotexts, size=8, weight="bold")
        plt.setp(texts, size=9)
        
        # Draw
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Close fig to save memory
        plt.close(fig)
