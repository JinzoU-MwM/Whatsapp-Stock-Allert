import pandas_ta as ta
import pandas as pd
import yfinance as yf

# Create a small sample dataframe
print("Downloading...")
df = yf.download("BBRI.JK", period="1mo", auto_adjust=False)

print("\n--- Columns Before Fix ---")
print(df.columns)

# Simulate the fix in technical_analysis.py
if isinstance(df.columns, pd.MultiIndex):
    # Try getting level 1 (Price Type) if level 0 is Ticker?
    # Or level 0 if it's Price Type?
    print("\nMultiIndex Detected.")
    print("Level 0:", df.columns.get_level_values(0))
    if len(df.columns.levels) > 1:
        print("Level 1:", df.columns.get_level_values(1))
    
    # Try the fix used in code
    df.columns = df.columns.get_level_values(0)

print("\n--- Columns After Fix ---")
print(df.columns)

# Run Bollinger Bands
try:
    df.ta.bbands(length=20, std=2, append=True)
    print("\nSuccess! Columns:")
    print(df.columns.tolist())
except Exception as e:
    print(f"\nError running bbands: {e}")
