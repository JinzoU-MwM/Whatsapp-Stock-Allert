import yfinance as yf
import pandas as pd

ticker = "BBRI.JK"
print(f"Checking data for {ticker}...")
stock = yf.Ticker(ticker)

try:
    print("\n--- Institutional Holders ---")
    print(stock.institutional_holders)
except Exception as e:
    print(f"Error: {e}")

try:
    print("\n--- Major Holders ---")
    print(stock.major_holders)
except Exception as e:
    print(f"Error: {e}")
    
try:
    print("\n--- Info Keys ---")
    info = stock.info
    # Check for foreign/float related keys
    relevant_keys = [k for k in info.keys() if 'float' in k.lower() or 'short' in k.lower() or 'held' in k.lower()]
    for k in relevant_keys:
        print(f"{k}: {info[k]}")
except Exception as e:
    print(f"Error: {e}")
