import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_stock_data(ticker, period="2y", interval="1d"):
    """Fetches stock data from yfinance. Auto-appends .JK if missing and initial fetch fails."""
    print(f"Fetching data for {ticker}...")
    
    df = pd.DataFrame()
    actual_ticker = ticker
    
    # Attempt 1: Try original ticker
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
    except Exception as e:
        print(f"Attempt 1 failed for {ticker}: {e}")

    # Check if data is truly empty or invalid
    if df.empty and "." not in ticker:
        ticker_jk = f"{ticker}.JK"
        print(f"Data empty/failed for {ticker}. Trying IDX suffix: {ticker_jk}...")
        try:
            df = yf.download(ticker_jk, period=period, interval=interval, progress=False, auto_adjust=False)
            if not df.empty:
                actual_ticker = ticker_jk
        except Exception as e:
             print(f"Error fetching {ticker_jk}: {e}")

    if df.empty:
        raise ValueError(f"No data found for ticker {ticker} (or {ticker}.JK). It may be delisted or invalid.")
    
    return df, actual_ticker

def analyze_technical(ticker):
    """
    Performs technical analysis using pandas_ta.
    Returns a dictionary with trend, support, resistance, key levels, VOLUME ANALYSIS, AND BANDARMOLOGY.
    """
    df, actual_ticker = get_stock_data(ticker)
    
    # Ensure MultiIndex columns are handled if yfinance returns them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Calculate Indicators
    # SMA 5, 8, 13 (as per user request)
    df.ta.sma(length=5, append=True)
    df.ta.sma(length=8, append=True)
    df.ta.sma(length=13, append=True)

    # EMA 20, 50, 200 (Keep for trend analysis logic)
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    
    # RSI (14)
    df.ta.rsi(length=14, append=True)
    
    # CCI (20)
    df.ta.cci(length=20, append=True)

    # MACD (Fast=12, Slow=26, Signal=9)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)

    # Bollinger Bands (Length=20, Std=2)
    # Using specific names if known, but relying on dynamic search below is safer
    df.ta.bbands(length=20, std=2, append=True)
    
    # Get latest values
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    price = latest['Close']
    rsi = latest['RSI_14']
    
    # Try to find CCI column dynamically to be safe
    cci_col = next((c for c in df.columns if c.startswith('CCI_')), 'CCI_20_0.015')
    cci = latest.get(cci_col, 0)
    
    ema20 = latest['EMA_20']
    ema50 = latest['EMA_50']
    volume = latest['Volume']

    # MACD Values
    macd = latest['MACD_12_26_9']
    macd_signal = latest['MACDs_12_26_9']
    macd_hist = latest['MACDh_12_26_9']

    # Bollinger Bands Dynamic Retrieval
    # We look for columns starting with BBU, BBL, BBM followed by 20_2.0
    cols = df.columns.tolist()
    
    # Defaults
    bb_upper = price
    bb_lower = price
    bb_mid = price
    
    # Find exact column names
    for c in cols:
        if c.startswith('BBU_20_2.0'):
            bb_upper = latest[c]
        elif c.startswith('BBL_20_2.0'):
            bb_lower = latest[c]
        elif c.startswith('BBM_20_2.0'):
            bb_mid = latest[c]

    # Handle Chart Generator Column Names
    # If pandas_ta generated BBU_20_2.0_2.0, we must ensure chart_generator knows about it
    # We will rename them to standard names if needed, or chart generator should also check dynamically.
    # For simplicity, let's alias them in the dataframe for the chart generator.
    for c in cols:
        if c.startswith('BBU_20_2.0'):
            df['BBU_20_2.0'] = df[c]
        elif c.startswith('BBL_20_2.0'):
            df['BBL_20_2.0'] = df[c]
    
    # --- VOLUME ANALYSIS ---
    avg_vol_20 = df['Volume'].tail(20).mean()
    
    vol_ratio = 0.0
    if avg_vol_20 > 0:
        vol_ratio = float(volume) / float(avg_vol_20)
        
    vol_status = "Normal"
    if vol_ratio > 2.5:
        vol_status = "Ledakan Volume (Spike Ekstrem)"
    elif vol_ratio > 1.5:
        vol_status = "Volume Tinggi (Akumulasi/Distribusi)"
    elif vol_ratio < 0.5:
        vol_status = "Volume Rendah (Sepi)"
    
    # --- SMART MONEY FLOW (Volume Analysis) ---
    # Renamed from "Bandarmology" to be more accurate (Proxy Method)
    
    price_change_1d = latest['Close'] - prev['Close']
    vol_spike = vol_ratio > 1.2
    
    sm_status = "Netral"
    sm_action = "Wait & See"
    
    if price_change_1d > 0:
        if vol_spike:
            sm_status = "AKUMULASI (Vol)"
            sm_action = "Big Money Masuk (Vol Tinggi)"
        else:
            sm_status = "Akumulasi Lemah"
            sm_action = "Ritel Mendominasi?"
    elif price_change_1d < 0:
        if vol_spike:
            sm_status = "DISTRIBUSI (Vol)"
            sm_action = "Big Money Keluar (Vol Tinggi)"
        else:
            sm_status = "Distribusi Lemah"
            sm_action = "Profit Taking Wajar"
    
    # --- TREND DETERMINATION ---
    trend = "Netral"
    if price > ema20 > ema50:
        trend = "Bullish (Naik)"
    elif price < ema20 < ema50:
        trend = "Bearish (Turun)"
    
    # MACD Trend
    macd_status = "Netral"
    if macd > macd_signal:
        macd_status = "Golden Cross (Bullish)" if macd < 0 else "Bullish Momentum"
    elif macd < macd_signal:
        macd_status = "Dead Cross (Bearish)" if macd > 0 else "Bearish Momentum"

    # BB Position
    bb_status = "Dalam Range"
    if price >= bb_upper:
        bb_status = "Overbought (Atas BB)"
    elif price <= bb_lower:
        bb_status = "Oversold (Bawah BB)"

    # --- MAJOR TREND (WEEKLY) ---
    # Resample to weekly to avoid extra API call
    try:
        logic = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
        df_weekly = df.resample('W').apply(logic)
        
        # Calculate Weekly EMAs
        df_weekly.ta.ema(length=20, append=True)
        df_weekly.ta.ema(length=50, append=True)
        
        if len(df_weekly) > 0:
            latest_weekly = df_weekly.iloc[-1]
            w_price = latest_weekly['Close']
            # Use .get because column might not exist if not enough data
            w_ema20 = latest_weekly.get('EMA_20', 0)
            w_ema50 = latest_weekly.get('EMA_50', 0)
            
            major_trend = "Netral"
            # Simple Trend Logic for Weekly
            if w_ema20 > 0 and w_ema50 > 0:
                if w_price > w_ema20 > w_ema50:
                    major_trend = "Sangat Bullish"
                elif w_price < w_ema20 < w_ema50:
                    major_trend = "Sangat Bearish"
                elif w_price > w_ema20:
                    major_trend = "Bullish"
                elif w_price < w_ema20:
                    major_trend = "Bearish"
            elif w_ema20 > 0:
                 if w_price > w_ema20:
                    major_trend = "Bullish"
                 else:
                    major_trend = "Bearish"
        else:
             major_trend = "Data Tidak Cukup"
    except Exception as e:
        print(f"Error calculating major trend: {e}")
        major_trend = "N/A"

    # --- INSTITUTIONAL/MAJOR HOLDERS (Proxy Context) ---
    major_holders = "N/A"
    try:
        # We need a fresh ticker object for holders
        t_obj = yf.Ticker(actual_ticker)
        # Try to get top 2 institutional or major holders
        holders = t_obj.institutional_holders
        if holders is not None and not holders.empty:
            top_holder = holders.iloc[0]['Holder']
            major_holders = f"{top_holder} (Inst)"
        else:
            # Fallback to major_holders
            m_holders = t_obj.major_holders
            if m_holders is not None and not m_holders.empty:
                # Often formatted as 0: value, 1: text
                # Try to parse sensible string
                major_holders = "Lihat Analisa AI" 
    except:
        major_holders = "Data Tidak Tersedia"

    # --- SUPPORT & RESISTANCE ---
    recent_high = df['High'].tail(20).max()
    recent_low = df['Low'].tail(20).min()
    
    # --- STOP LOSS & TARGET ---
    stop_loss = price * 0.95
    target = price + (price - stop_loss) * 1.5
    
    # --- FIBONACCI RETRACEMENT (Auto-Swing High/Low last 120 days) ---
    # We use a 6-month lookback for significant levels
    lookback = 120
    if len(df) > lookback:
        fib_slice = df.tail(lookback)
    else:
        fib_slice = df
        
    fib_high = fib_slice['High'].max()
    fib_low = fib_slice['Low'].min()
    fib_diff = fib_high - fib_low
    
    # Calculate Levels
    fib_levels = {
        0.0: fib_low,
        0.236: fib_low + (0.236 * fib_diff),
        0.382: fib_low + (0.382 * fib_diff),
        0.5: fib_low + (0.5 * fib_diff),
        0.618: fib_low + (0.618 * fib_diff),
        0.786: fib_low + (0.786 * fib_diff),
        1.0: fib_high
    }

    return {
        "ticker": actual_ticker,
        "df_daily": df, # Added for Chart Generation
        "price": price,
        "trend": trend,
        "major_trend": major_trend, # Added for Agent & UI
        "rsi": rsi,
        "cci": cci,
        "fib_levels": fib_levels, # Pass to chart generator
        "volume": volume,
        "avg_volume": avg_vol_20,
        "vol_status": vol_status,
        "vol_ratio": vol_ratio,
        "bandar_status": sm_status, # Kept key name for compat, value updated
        "bandar_action": sm_action,
        "major_holders": major_holders,
        "support": recent_low,
        "resistance": recent_high,
        "ema20": ema20,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "macd_status": macd_status,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "bb_status": bb_status,
        "stop_loss": stop_loss,
        "target": target
    }
