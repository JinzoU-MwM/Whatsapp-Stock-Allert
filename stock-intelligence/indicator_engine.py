import pandas_ta as ta
import pandas as pd
import numpy as np

def add_indicators(df):
    """
    Adds technical indicators to the DataFrame inplace.
    """
    # 1. Moving Averages
    df.ta.sma(length=5, append=True)
    df.ta.sma(length=8, append=True)
    df.ta.sma(length=13, append=True)
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    
    # 2. Momentum & Oscillators
    df.ta.rsi(length=14, append=True)
    df.ta.cci(length=20, append=True)
    df.ta.stoch(append=True)
    
    # 3. Trend Strength & Volatility
    df.ta.adx(length=14, append=True)
    df.ta.atr(length=14, append=True)
    
    # 4. Volume
    df.ta.mfi(length=14, append=True)
    df.ta.obv(append=True)
    if 'OBV' in df.columns:
        df['OBV_EMA'] = ta.ema(df['OBV'], length=20)
    
    # 5. MACD & Bollinger
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    
    # 6. Candlestick Patterns
    patterns = ["doji", "engulfing", "hammer", "shooting_star"]
    try:
        df.ta.cdl_pattern(name=patterns, append=True)
    except Exception as e:
        print(f"Warning: CDL Pattern detection failed: {e}")

    # 7. Supertrend
    st_length = 10
    st_multiplier = 3.0
    df.ta.supertrend(length=st_length, multiplier=st_multiplier, append=True)
    
    # Handle Chart Generator Column Names (Aliasing)
    cols = df.columns.tolist()
    for c in cols:
        if c.startswith('BBU_20_2.0'): df['BBU_20_2.0'] = df[c]
        elif c.startswith('BBL_20_2.0'): df['BBL_20_2.0'] = df[c]

    return df

def calculate_pivots(latest_candle):
    """
    Calculates Standard Pivot Points.
    """
    pivots = {}
    try:
        p_high = float(latest_candle['High'])
        p_low = float(latest_candle['Low'])
        p_close = float(latest_candle['Close'])
        
        pp = (p_high + p_low + p_close) / 3
        r1 = (2 * pp) - p_low
        s1 = (2 * pp) - p_high
        r2 = pp + (p_high - p_low)
        s2 = pp - (p_high - p_low)
        
        pivots = {"pivot": pp, "r1": r1, "s1": s1, "r2": r2, "s2": s2}
    except:
        pass
    return pivots

def calculate_fibonacci(df, lookback=120):
    """
    Calculates Fibonacci Retracement Levels based on recent High/Low.
    """
    fib_slice = df.tail(lookback) if len(df) > lookback else df
    fib_high = fib_slice['High'].max()
    fib_low = fib_slice['Low'].min()
    fib_diff = fib_high - fib_low
    
    return {
        0.0: fib_low, 
        0.236: fib_low + (0.236*fib_diff), 
        0.382: fib_low + (0.382*fib_diff),
        0.5: fib_low + (0.5*fib_diff), 
        0.618: fib_low + (0.618*fib_diff),
        0.786: fib_low + (0.786*fib_diff), 
        1.0: fib_high
    }

def get_candlestick_summary(df, latest_idx=-1):
    """ Extract human readable pattern names from CDL columns. """
    latest = df.iloc[latest_idx]
    candle_note = "Tidak Ada Pola Signifikan"
    try:
        cdl_cols = [c for c in df.columns if c.startswith('CDL_')]
        found_patterns = []
        for c in cdl_cols:
            if latest[c] != 0:
                pat_name = c.split('_')[1].title()
                found_patterns.append(pat_name)
        if found_patterns:
            candle_note = ", ".join(found_patterns)
    except:
        pass
    return candle_note
