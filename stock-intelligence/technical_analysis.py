import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_stock_data(ticker, period="2y", interval="1d"):
    """Fetches stock data from yfinance. Auto-appends .JK if missing and initial fetch fails."""
    print(f"Fetching data for {ticker}...")
    
    # Try original ticker first
    # auto_adjust=False ensures we get OHLC data as is (classic TA)
    # This also silences the yfinance FutureWarning.
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
    
    actual_ticker = ticker

    # If empty and no suffix, try adding .JK (Indonesia)
    if df.empty and "." not in ticker:
        ticker_jk = f"{ticker}.JK"
        print(f"Data empty for {ticker}. Trying IDX suffix: {ticker_jk}...")
        try:
            df = yf.download(ticker_jk, period=period, interval=interval, progress=False, auto_adjust=False)
            if not df.empty:
                actual_ticker = ticker_jk
        except Exception as e:
             print(f"Error fetching {ticker_jk}: {e}")

    if df.empty:
        raise ValueError(f"No data found for ticker {ticker} (or {ticker}.JK)")
    
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
    # EMA 20, 50, 200
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    
    # RSI
    df.ta.rsi(length=14, append=True)
    
    # Get latest values
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    price = latest['Close']
    rsi = latest['RSI_14']
    ema20 = latest['EMA_20']
    ema50 = latest['EMA_50']
    volume = latest['Volume']
    
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
    
    return {
        "ticker": actual_ticker,
        "df_daily": df, # Added for Chart Generation
        "price": price,
        "trend": trend,
        "major_trend": major_trend, # Added for Agent & UI
        "rsi": rsi,
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
        "stop_loss": stop_loss,
        "target": target
    }
