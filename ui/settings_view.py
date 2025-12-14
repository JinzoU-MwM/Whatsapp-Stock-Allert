import customtkinter as ctk
from tkinter import messagebox

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # Container
        self.container = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(self.container, text="APP SETTINGS", font=("Arial", 20, "bold"), text_color="#2CC985").pack(pady=20)
        
        # Form Container
        self.form_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=40)
        
        # -- Fields --
        
        # Google API Key
        ctk.CTkLabel(self.form_frame, text="Google Gemini API Key", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", pady=(10, 0))
        self.entry_google = ctk.CTkEntry(self.form_frame, width=400, placeholder_text="Enter your Gemini API Key")
        self.entry_google.pack(anchor="w", pady=(5, 10), fill="x")
        
        # Serper API Key
        ctk.CTkLabel(self.form_frame, text="Serper API Key (News)", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", pady=(10, 0))
        self.entry_serper = ctk.CTkEntry(self.form_frame, width=400, placeholder_text="Enter your Serper API Key")
        self.entry_serper.pack(anchor="w", pady=(5, 10), fill="x")
        
        # GoAPI Key
        ctk.CTkLabel(self.form_frame, text="GoAPI Key (Bandarmology - Optional)", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", pady=(10, 0))
        self.entry_goapi = ctk.CTkEntry(self.form_frame, width=400, placeholder_text="Enter your GoAPI Key")
        self.entry_goapi.pack(anchor="w", pady=(5, 10), fill="x")
        
        # Target Phone
        ctk.CTkLabel(self.form_frame, text="Target WhatsApp Phone / Group ID", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", pady=(10, 0))
        self.entry_phone = ctk.CTkEntry(self.form_frame, width=400, placeholder_text="e.g. 6281234567890@c.us or 12345@g.us")
        self.entry_phone.pack(anchor="w", pady=(5, 10), fill="x")
        
        # AI Model Selection
        ctk.CTkLabel(self.form_frame, text="AI Model (Gemini)", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", pady=(10, 0))
        self.model_var = ctk.StringVar(value="gemini-2.0-flash-exp")
        self.combo_model = ctk.CTkComboBox(self.form_frame, width=400, variable=self.model_var, 
                                         values=["gemini-2.0-flash-exp (Free/Fast)", "gemini-1.5-pro (Paid/Deep)", "gemini-1.5-flash (Balanced)"],
                                         state="readonly") # Prevent manual typing
        self.combo_model.pack(anchor="w", pady=(5, 10), fill="x")
        
        # Save Button
        self.btn_save = ctk.CTkButton(self.container, text="SAVE CONFIGURATION 💾", 
                                    font=("Arial", 14, "bold"), height=40,
                                    fg_color="#1F6AA5", hover_color="#144870",
                                    command=self.save_settings)
        self.btn_save.pack(pady=30, padx=40, fill="x")

    def load_data(self):
        config = self.controller.get_config()
        
        self.entry_google.delete(0, "end")
        self.entry_google.insert(0, config.get("GOOGLE_API_KEY", ""))
        
        self.entry_serper.delete(0, "end")
        self.entry_serper.insert(0, config.get("SERPER_API_KEY", ""))
        
        self.entry_goapi.delete(0, "end")
        self.entry_goapi.insert(0, config.get("GOAPI_API_KEY", ""))
        
        self.entry_phone.delete(0, "end")
        self.entry_phone.insert(0, config.get("TARGET_PHONE", ""))
        
        # Load model preference
        current_model = config.get("AI_MODEL", "gemini-2.0-flash-exp")
        # Match with combobox values (simple check)
        if "pro" in current_model: self.model_var.set("gemini-1.5-pro (Paid/Deep)")
        elif "1.5-flash" in current_model: self.model_var.set("gemini-1.5-flash (Balanced)")
        else: self.model_var.set("gemini-2.0-flash-exp (Free/Fast)")

    def save_settings(self):
        # Extract clean model name from combobox value (remove description)
        raw_model = self.model_var.get()
        clean_model = raw_model.split(" ")[0] # "gemini-2.0-flash-exp"
        
        new_config = {
            "GOOGLE_API_KEY": self.entry_google.get().strip(),
            "SERPER_API_KEY": self.entry_serper.get().strip(),
            "GOAPI_API_KEY": self.entry_goapi.get().strip(),
            "TARGET_PHONE": self.entry_phone.get().strip(),
            "AI_MODEL": clean_model
        }
        
        if self.controller.save_config(new_config):
            messagebox.showinfo("Success", "Configuration saved successfully!\nRestart may be required for some changes to take effect.")
        else:
            messagebox.showerror("Error", "Failed to save configuration.")
