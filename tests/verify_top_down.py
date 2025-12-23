import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence')))

# Since we added stock-intelligence to path, we import directly from the module
from app_controller import StockAppController
from dotenv import load_dotenv

load_dotenv()

def mock_logger(msg):
    # Filter only relevant logs
    if "Bandarmology" in msg or "TRADING PLAN" in msg or "AI" in msg or "Map" in msg or "Trigger" in msg:
        print(f"[LOG] {msg}")

def verify_logic():
    print("--- Verifying Top-Down Logic & Trading Plan ---")
    
    controller = StockAppController(log_callback=mock_logger)
    
    # Analyze a liquid stock likely to have data
    ticker = "BBRI" 
    
    try:
        msg, chart_path, score = controller.run_analysis(ticker, timeframe="daily")
        
        print("\n--- FINAL MESSAGE GENERATED ---")
        print(msg)
        print("-------------------------------")
        
        # Validation
        checks = {
            "Trading Plan": "TRADING PLAN" in msg,
            "Disclaimer": "Disclaimer: Plan ini auto-generated" in msg,
            "Bandar Forensics": "FORENSIK BANDAR" in msg
        }
        
        all_pass = True
        for k, v in checks.items():
            status = "✅ PASS" if v else "❌ FAIL"
            print(f"{k}: {status}")
            if not v: all_pass = False
            
        if all_pass:
            print("\nSUCCESS: All logic updates verified in output.")
        else:
            print("\nFAILURE: Some components missing from output.")
            
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_logic()
