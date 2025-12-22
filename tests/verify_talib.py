
import sys
import os

try:
    import talib
    print(f"Success: TA-Lib {talib.__version__} imported.")
    print(f"Functions available: {len(talib.get_functions())}")
except Exception as e:
    print(f"Error importing TA-Lib: {e}")
