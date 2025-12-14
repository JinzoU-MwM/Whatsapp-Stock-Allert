import customtkinter as ctk

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, controller, app):
        super().__init__(parent, width=220, corner_radius=0)
        self.controller = controller
        self.app = app
        
        # Grid Configuration
        self.grid_rowconfigure(20, weight=1) # Spacer at bottom to push logout down
        self.grid_columnconfigure(0, weight=1)

        self.setup_ui()
        self.update_lists()

    def setup_ui(self):
        # 1. Logo / Title
        self.logo_label = ctk.CTkLabel(self, text="STOCK\nINTELLIGENCE", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 2. Navigation Menu
        self.nav_label = ctk.CTkLabel(self, text="MENU", font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaa")
        self.nav_label.grid(row=1, column=0, padx=20, pady=(5, 5), sticky="w")

        # Market Data Button (Active by default)
        self.btn_nav_market = ctk.CTkButton(self, text="📊 MARKET DATA", 
                                          fg_color="#1F6AA5", hover_color="#144870",
                                          anchor="w", width=180, height=30,
                                          command=self.app.show_market_view)
        self.btn_nav_market.grid(row=2, column=0, padx=20, pady=2)

        # Portfolio Button (Inactive by default)
        self.btn_nav_portfolio = ctk.CTkButton(self, text="💼 PORTFOLIO", 
                                             fg_color="transparent", hover_color="#333", border_width=1, border_color="gray", text_color="gray",
                                             anchor="w", width=180, height=30,
                                             command=self.app.show_portfolio_view)
        self.btn_nav_portfolio.grid(row=3, column=0, padx=20, pady=2)

        # 3. Status
        self.status_label = ctk.CTkLabel(self, text="SYSTEM: INIT...", text_color="gray", font=ctk.CTkFont(size=10))
        self.status_label.grid(row=4, column=0, padx=20, pady=(10, 5))
        
        # 4. QR Button (Hidden by default or shown if needed)
        self.qr_btn = ctk.CTkButton(self, text="LINK WHATSAPP", command=self.app.show_qr_modal, 
                                  fg_color="#333", border_width=1, border_color="gray", width=180, height=30)
        self.qr_btn.grid(row=5, column=0, padx=20, pady=5)
        
        # 5. Favorites Section
        self.fav_label = ctk.CTkLabel(self, text="FAVORITE TICKERS", font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaa")
        self.fav_label.grid(row=6, column=0, padx=20, pady=(15, 5), sticky="w")

        # REDUCED HEIGHT DRASTICALLY (140 -> 100)
        self.fav_frame = ctk.CTkScrollableFrame(self, width=180, height=100, fg_color="transparent")
        self.fav_frame.grid(row=7, column=0, padx=10, pady=2)
        
        # 6. History Section
        self.hist_label = ctk.CTkLabel(self, text="RECENT HISTORY", font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaa")
        self.hist_label.grid(row=8, column=0, padx=20, pady=(15, 5), sticky="w")
        
        # REDUCED HEIGHT DRASTICALLY (120 -> 80)
        self.hist_frame = ctk.CTkScrollableFrame(self, width=180, height=80, fg_color="transparent")
        self.hist_frame.grid(row=9, column=0, padx=10, pady=2)
        
        # 20. Logout Button (Sticky Bottom)
        self.logout_btn = ctk.CTkButton(self, text="DISCONNECT WA", command=self.app.logout_whatsapp, 
                                      fg_color="#330000", hover_color="#550000", border_width=1, border_color="#550000",
                                      width=180, height=35)
        
        # Reduced bottom padding (20 -> 10)
        self.logout_btn.grid(row=21, column=0, padx=20, pady=(5, 10), sticky="s")
        self.logout_btn.grid_remove() # Hidden initially

    def update_lists(self):
        # Refresh Favorites
        for widget in self.fav_frame.winfo_children():
            widget.destroy()
            
        favorites = self.controller.get_favorites()
        if not favorites:
            ctk.CTkLabel(self.fav_frame, text="No Favorites", text_color="gray", font=("Arial", 10)).pack()
        else:
            for ticker in favorites:
                row = ctk.CTkFrame(self.fav_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                # Load Ticker on Click
                btn = ctk.CTkButton(row, text=f"★ {ticker}", width=120, height=28, anchor="w", fg_color="transparent", hover_color="#333",
                                  font=ctk.CTkFont(size=12),
                                  command=lambda t=ticker: self.app.load_ticker(t))
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
                                  command=lambda t=ticker: self.app.load_ticker(t))
                btn.pack(fill="x", pady=1)

    def remove_favorite(self, ticker):
        self.controller.remove_favorite(ticker)
        self.update_lists()
        # If current view is market, update button state there too?
        if hasattr(self.app, "market_view") and hasattr(self.app.market_view, "update_favorite_btn_state"):
             self.app.market_view.update_favorite_btn_state()

    def update_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)

    def show_qr_btn(self, show=True):
        if show:
            self.qr_btn.grid()
            self.logout_btn.grid_remove()
        else:
            self.qr_btn.grid_remove()
            self.logout_btn.grid()
