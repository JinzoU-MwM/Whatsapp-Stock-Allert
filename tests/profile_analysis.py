
import time
import sys
import os

# Setup Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from technical_analysis import analyze_technical, get_stock_data, get_valuation_data
from quant_engine import QuantAnalyzer
try:
    from goapi_client import GoApiClient
except:
    GoApiClient = None

def profile_technical(ticker):
    print(f"\n--- Profiling Technical: {ticker} ---")
    
    t0 = time.time()
    # 1. Get Stock Data Only
    try:
        df, actual = get_stock_data(ticker)
        t1 = time.time()
        print(f"get_stock_data: {t1-t0:.4f}s")
    except Exception as e:
        print(f"get_stock_data failed: {e}")
        t1 = time.time()

    # 2. Valuation Only
    try:
        val = get_valuation_data(ticker)
        t2 = time.time()
        print(f"get_valuation_data: {t2-t1:.4f}s")
    except Exception as e:
        print(f"get_valuation_data failed: {e}")
        t2 = time.time()

    # 3. Full Analyze Technical (includes overhead)
    try:
        res = analyze_technical(ticker)
        t3 = time.time()
        print(f"analyze_technical (Total): {t3-t2:.4f}s")
    except Exception as e:
        print(f"analyze_technical failed: {e}")

if __name__ == "__main__":
    profile_technical("BBCA")
    profile_technical("COAL") # Test validity of 4-letter optimization

    print("\n--- Profiling Full Controller Run (Parallel Check) ---")
    from app_controller import StockAppController
    
    def mock_log(msg): pass
    def mock_prog(p): pass
    
    ctrl = StockAppController(log_callback=mock_log)
    t_start = time.time()
    try:
        # Run full analysis (note: this includes AI time which we can't speed up easily, 
        # but we want to see if the DATA FETCHING part is faster)
        # We can't easily skip AI without mocking, but total time reduction is what user cares about.
        ctrl.run_analysis("BBCA", progress_callback=mock_prog)
        t_end = time.time()
        print(f"Full run_analysis (BBCA): {t_end-t_start:.4f}s")
    except Exception as e:
        print(f"Controller run failed: {e}")
