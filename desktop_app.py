import sys
import os
import traceback
import tkinter as tk
from tkinter import messagebox

# 1. Setup Path to include 'stock-intelligence' logic
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'stock-intelligence'))

def main():
    try:
        # 2. Import App
        from ui.app import StockSignalApp
        
        # 3. Launch
        app = StockSignalApp()
        app.mainloop()
        
    except Exception as e:
        # 4. Error Handling (Show popup even if console is hidden)
        root = tk.Tk()
        root.withdraw()
        error_text = f"Startup Error:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        messagebox.showerror("StockSignal Crash", error_text)
        root.destroy()
        sys.exit(1)

if __name__ == "__main__":
    main()
