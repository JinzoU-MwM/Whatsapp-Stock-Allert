
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence')))

import technical_analysis

tickers = ['BBCA.JK', 'GOTO.JK', 'ADRO.JK', 'ITMG.JK']

print(f"{'Ticker':<10} | {'PBV (Fixed)':<15} | {'Valuation Status':<25}")
print("-" * 65)

for t in tickers:
    try:
        val_data = technical_analysis.get_valuation_data(t)
        pbv = val_data.get('pbv', 0)
        status = val_data.get('valuation_status', 'N/A')
        
        print(f"{t:<10} | {pbv:<15.2f} | {status:<25}")
        
    except Exception as e:
        print(f"{t:<10} | Error: {e}")
