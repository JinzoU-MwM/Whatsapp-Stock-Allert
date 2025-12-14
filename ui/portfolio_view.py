import customtkinter as ctk
import threading
from tkinter import messagebox

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
        
        ctk.CTkButton(input_row, text="+ ADD / UPDATE", width=120, fg_color="#1F6AA5", command=self.add_portfolio_entry).pack(side="left", padx=10)

        # 2. Table Area
        self.table_frame = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color="#111", border_width=1, border_color="#333")
        self.table_frame.grid(row=1, column=0, sticky="nsew")
        self.table_frame.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)
        
        # Headers
        headers = ["TICKER", "AVG PRICE", "LOTS", "CUR. PRICE", "VALUE (RP)", "P/L %", "ACTION"]
        for idx, h in enumerate(headers):
            ctk.CTkLabel(self.table_frame, text=h, font=("Arial", 11, "bold"), text_color="gray").grid(row=0, column=idx, pady=10, sticky="ew")

        # 3. Footer Summary
        self.footer_frame = ctk.CTkFrame(self, height=60, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.footer_frame.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        
        self.total_val_label = ctk.CTkLabel(self.footer_frame, text="Total Equity: Rp 0", font=("Arial", 14, "bold"))
        self.total_val_label.pack(side="left", padx=20, pady=15)
        
        self.total_pl_label = ctk.CTkLabel(self.footer_frame, text="Total P/L: Rp 0 (0%)", font=("Arial", 14, "bold"))
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
        # Clear existing rows (keep header row 0)
        for widget in self.table_frame.winfo_children():
            info = widget.grid_info()
            if int(info['row']) > 0:
                widget.destroy()
        
        # Fetch Data (Threaded to avoid freeze on price fetch)
        def _fetch():
            data = self.controller.get_portfolio_summary()
            self.after(0, lambda: self._populate_table(data))
            
        threading.Thread(target=_fetch, daemon=True).start()

    def _populate_table(self, data):
        total_equity = 0
        total_pl_val = 0
        total_invest = 0
        
        for idx, item in enumerate(data, start=1):
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
            
            # Color
            pl_color = "#00ff00" if pl_pct >= 0 else "#ff0000"
            
            # Row Widgets
            ctk.CTkLabel(self.table_frame, text=tick, font=("Arial", 12, "bold")).grid(row=idx, column=0, pady=5)
            ctk.CTkLabel(self.table_frame, text=f"{avg:,.0f}").grid(row=idx, column=1, pady=5)
            ctk.CTkLabel(self.table_frame, text=f"{lots}").grid(row=idx, column=2, pady=5)
            ctk.CTkLabel(self.table_frame, text=f"{curr:,.0f}").grid(row=idx, column=3, pady=5)
            ctk.CTkLabel(self.table_frame, text=f"{mkt_val:,.0f}").grid(row=idx, column=4, pady=5)
            ctk.CTkLabel(self.table_frame, text=f"{pl_pct:+.2f}%", text_color=pl_color).grid(row=idx, column=5, pady=5)
            
            ctk.CTkButton(self.table_frame, text="✕", width=30, height=25, fg_color="#500", command=lambda t=tick: self.delete_portfolio_entry(t)).grid(row=idx, column=6, pady=5)

        # Update Footer
        total_pl_pct = (total_pl_val / total_invest * 100) if total_invest > 0 else 0
        pl_color = "#00ff00" if total_pl_val >= 0 else "#ff0000"
        
        self.total_val_label.configure(text=f"Total Equity: Rp {total_equity:,.0f}")
        self.total_pl_label.configure(text=f"Total P/L: Rp {total_pl_val:,.0f} ({total_pl_pct:+.2f}%)", text_color=pl_color)
