import yfinance as yf
import pandas_ta as ta
import pandas as pd
import numpy as np
import os
import datetime
try:
    from goapi_client import GoApiClient
except ImportError:
    GoApiClient = None

def get_stock_data(ticker, period="2y", interval="1d"):
    """
    Fetches stock data.
    Prioritizes GoAPI if key is present, falls back to yfinance.
    """
    print(f"Fetching data for {ticker}...")
    
    df = pd.DataFrame()
    actual_ticker = ticker
    
    # --- Attempt 1: GoAPI ---
    goapi_key = os.getenv("GOAPI_API_KEY")
    # Disabled temporarily in favor of yfinance for price data as GoAPI seems delayed (e.g. returns Friday data on Monday)
    # Re-enable if GoAPI provides truly realtime data in future.
    # We still use GoAPI for Bandarmology (Broker Summary) later in the main flow.
    """
    if goapi_key and GoApiClient and interval == "1d":
        print(f"   [Source] Attempting GoAPI for {ticker}...")
        try:
            client = GoApiClient(goapi_key)
            ...
        except Exception as e:
            print(f"   [Source] GoAPI Failed: {e}. Fallback to yfinance.")
    """

    # --- Attempt 2: YFinance (Primary Source for Price) ---
    if df.empty:
        print(f"   [Source] Attempting yfinance for {ticker}...")
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
        except Exception as e:
            print(f"   [Source] yfinance failed for {ticker}: {e}")

        # Check if data is truly empty or invalid
        if df.empty and "." not in ticker:
            ticker_jk = f"{ticker}.JK"
            print(f"   [Source] Data empty/failed for {ticker}. Trying IDX suffix: {ticker_jk}...")
            try:
                df = yf.download(ticker_jk, period=period, interval=interval, progress=False, auto_adjust=False)
                if not df.empty:
                    actual_ticker = ticker_jk
            except Exception as e:
                 print(f"   [Source] Error fetching {ticker_jk}: {e}")

    if df.empty:
        raise ValueError(f"No data found for ticker {ticker} (or {ticker}.JK). It may be delisted or invalid.")

    # Ensure columns are flat (handle MultiIndex from yf.download in recent versions)
    # Must be done BEFORE merging real-time data
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # --- Attempt 3: Merge Real-Time Price (GoAPI Latest) ---
    # Only applicable for daily timeframe
    if goapi_key and GoApiClient and interval == "1d" and not df.empty:
         try:
            client = GoApiClient(goapi_key)
            latest = client.get_latest_price(ticker)
            if latest:
                latest_date_str = latest.get('date')
                if latest_date_str:
                    latest_date = pd.to_datetime(latest_date_str)
                    last_hist_date = df.index[-1]
                    
                    # If latest price is newer than historical, append it
                    if latest_date > last_hist_date:
                        print(f"   [Source] Found newer real-time data for {latest_date_str}. Appending...")
                        new_row = pd.DataFrame([{
                            'Open': float(latest.get('open', 0)),
                            'High': float(latest.get('high', 0)),
                            'Low': float(latest.get('low', 0)),
                            'Close': float(latest.get('close', 0)),
                            'Volume': float(latest.get('volume', 0))
                        }], index=[latest_date])
                        
                        df = pd.concat([df, new_row])
                        print(f"   [Source] Data updated. Last candle: {latest_date_str}")
                    elif latest_date == last_hist_date:
                        # Optional: Update the last candle if it's the same day (intra-day update)
                        # For now, we assume historical EOD is good enough, but we could overwrite.
                        pass
         except Exception as e:
             print(f"   [Source] Real-time merge failed: {e}")

    return df, actual_ticker

def analyze_technical(ticker, timeframe="daily"):
    """
    Performs technical analysis using pandas_ta.
    Returns a dictionary with trend, support, resistance, key levels, VOLUME ANALYSIS, AND BANDARMOLOGY.
    """
    # Map timeframe to yfinance params
    if timeframe == "weekly":
        df, actual_ticker = get_stock_data(ticker, period="2y", interval="1wk")
    elif timeframe == "monthly":
        df, actual_ticker = get_stock_data(ticker, period="5y", interval="1mo")
    else:
        df, actual_ticker = get_stock_data(ticker, period="1y", interval="1d") # Default daily
    
    # Ensure MultiIndex columns are handled if yfinance returns them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # --- ADVANCED INDICATORS ---
    
    # 1. Moving Averages
    df.ta.sma(length=5, append=True)
    df.ta.sma(length=8, append=True)
    df.ta.sma(length=13, append=True)
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    
    # 2. Momentum & Oscillators
    df.ta.rsi(length=14, append=True)
    df.ta.cci(length=20, append=True)
    df.ta.stoch(append=True) # Returns STOCHk_14_3_3, STOCHd_14_3_3
    
    # 3. Trend Strength & Volatility
    df.ta.adx(length=14, append=True) # Returns ADX_14, DMP_14, DMN_14
    df.ta.atr(length=14, append=True) # Returns ATR_14
    
    # 4. Volume & Smart Money
    df.ta.mfi(length=14, append=True) # Returns MFI_14
    df.ta.obv(append=True) # Returns OBV
    # Calculate OBV EMA for trend signal
    # We need to explicitly access the OBV column since column name is just 'OBV'
    if 'OBV' in df.columns:
        df['OBV_EMA'] = ta.ema(df['OBV'], length=20)
    
    # 5. MACD & Bollinger Bands
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    
    # 6. Candlestick Patterns
    # We'll detect a few key patterns
    patterns = ["doji", "engulfing", "hammer", "shooting_star"]
    try:
        df.ta.cdl_pattern(name=patterns, append=True)
    except Exception as e:
        print(f"Warning: CDL Pattern detection failed (requires TA-Lib sometimes): {e}")

    # --- EXTRACT LATEST DATA ---
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    price = latest['Close']
    volume = latest['Volume']
    
    # Get Indicator Values (Default from Local Calc)
    rsi = latest.get('RSI_14', 50)
    cci_col = next((c for c in df.columns if c.startswith('CCI_')), 'CCI_20_0.015')
    cci = latest.get(cci_col, 0)
    
    adx = latest.get('ADX_14', 0)
    atr = latest.get('ATRr_14', latest.get('ATR_14', price * 0.02)) # Fallback
    
    mfi = latest.get('MFI_14', 50)
    obv = latest.get('OBV', 0)
    obv_ema = latest.get('OBV_EMA', 0)
    
    stoch_k = latest.get('STOCHk_14_3_3', 50)
    stoch_d = latest.get('STOCHd_14_3_3', 50)

    ema20 = latest['EMA_20']
    ema50 = latest['EMA_50']
    
    # --- GOAPI INDICATORS MERGE (Hybrid) ---
    # Overwrite key metrics with official GoAPI data if available
    goapi_key = os.getenv("GOAPI_API_KEY")
    if goapi_key and GoApiClient and timeframe == "daily":
        try:
            client = GoApiClient(goapi_key)
            go_inds = client.get_indicators(ticker)
            if go_inds:
                print(f"   [Source] Merging GoAPI Indicators for {ticker}...")
                # Map GoAPI fields to local variables
                if 'RSI' in go_inds: rsi = float(go_inds['RSI'])
                if 'EMA20' in go_inds: ema20 = float(go_inds['EMA20'])
                if 'EMA50' in go_inds: ema50 = float(go_inds['EMA50'])
                # GoAPI also has MA, likely used for other checks
                
                # Note: We don't overwrite MFI, ADX, MACD as GoAPI basic response 
                # might not have them (based on probe). We keep local calc for those.
        except Exception as e:
            print(f"   [Source] GoAPI Indicator Fetch Failed: {e}")

    # MACD Values
    macd = latest['MACD_12_26_9']
    macd_signal = latest['MACDs_12_26_9']
    macd_hist = latest['MACDh_12_26_9']

    # Bollinger Bands
    cols = df.columns.tolist()
    bb_upper = price
    bb_lower = price
    bb_mid = price
    
    for c in cols:
        if c.startswith('BBU_20_2.0'): bb_upper = latest[c]
        elif c.startswith('BBL_20_2.0'): bb_lower = latest[c]
        elif c.startswith('BBM_20_2.0'): bb_mid = latest[c]

    # Handle Chart Generator Column Names (Aliasing)
    for c in cols:
        if c.startswith('BBU_20_2.0'): df['BBU_20_2.0'] = df[c]
        elif c.startswith('BBL_20_2.0'): df['BBL_20_2.0'] = df[c]
    
    # --- VOLUME & LIQUIDITY ANALYSIS (Enhanced) ---
    avg_vol_20 = df['Volume'].tail(20).mean()
    
    # Handle potentially 0 volume (e.g. morning session start) by checking previous candle if needed
    curr_vol = float(volume)
    if curr_vol <= 0 and len(df) > 1:
        curr_vol = float(prev['Volume']) # Fallback to previous day if today is 0
        
    vol_ratio = 0.0
    if avg_vol_20 > 0:
        vol_ratio = curr_vol / float(avg_vol_20)
        
    # Absolute Liquidity (Value = Price * Volume)
    # Assuming YFinance volume is in Shares. 
    tx_value = float(price) * curr_vol
    
    # Thresholds (IDR)
    # 20 Billion IDR = 20,000,000,000
    HIGH_LIQUIDITY_THRESHOLD = 20_000_000_000
    
    vol_status = "Normal" # Default
    
    if vol_ratio > 2.5:
        vol_status = "EXPLOSIVE VOL (Spike)"
    elif vol_ratio > 1.2:
        vol_status = "High Volume"
    elif vol_ratio < 0.6:
        vol_status = "Low / Dry"
    else:
        # Normal RVol range (0.6 - 1.2)
        # Check absolute liquidity
        if tx_value > HIGH_LIQUIDITY_THRESHOLD:
            vol_status = "High Liquidity (Active)"
        else:
            vol_status = "Normal (Retail)"
    
    # --- SMART MONEY / BANDARMOLOGY (Refined) ---
    # Renamed from "Bandarmology" to be more accurate (Proxy Method)
    
    price_change_1d = latest['Close'] - prev['Close']
    vol_spike = vol_ratio > 1.2
    
    sm_status = "Netral"
    sm_action = "Wait & See"
    
    mfi_bullish = mfi > 50 and mfi > prev.get('MFI_14', 50)
    obv_bullish = obv > obv_ema
    
    if price_change_1d > 0:
        if vol_ratio > 1.2 and (mfi_bullish or obv_bullish):
            sm_status = "AKUMULASI KUAT"
            sm_action = "Big Money Masuk (Vol + MFI)"
        elif vol_ratio > 1.0:
            sm_status = "Akumulasi Ringan"
            sm_action = "Follow Trend"
        else:
            sm_status = "Rebound Tanpa Volume"
            sm_action = "Hati-hati Bull Trap"
    elif price_change_1d < 0:
        if vol_ratio > 1.2 and (not mfi_bullish or not obv_bullish):
            sm_status = "DISTRIBUSI KUAT"
            sm_action = "Big Money Keluar (Vol + MFI)"
        elif vol_ratio > 1.0:
            sm_status = "Distribusi Ringan"
            sm_action = "Profit Taking?"
        else:
            sm_status = "Koreksi Wajar"
            sm_action = "Pantau Support"

    # --- TREND DETERMINATION (Refined with ADX) ---
    trend = "Netral"
    adx_strength = "Lemah"
    if adx > 25: adx_strength = "Kuat"
    elif adx > 50: adx_strength = "Sangat Kuat"
    
    if price > ema20 > ema50:
        trend = f"Bullish ({adx_strength})"
    elif price < ema20 < ema50:
        trend = f"Bearish ({adx_strength})"
    else:
        trend = "Sideways / Konsolidasi"
    
    # MACD Status
    macd_status = "Netral"
    if macd > macd_signal:
        macd_status = "Golden Cross (Bullish)" if macd < 0 else "Bullish Momentum"
    elif macd < macd_signal:
        macd_status = "Dead Cross (Bearish)" if macd > 0 else "Bearish Momentum"

    # BB Position
    bb_status = "Dalam Range"
    if price >= bb_upper: bb_status = "Overbought (Atas BB)"
    elif price <= bb_lower: bb_status = "Oversold (Bawah BB)"

    # --- CANDLESTICK PATTERNS ---
    candle_note = "Tidak Ada Pola Signifikan"
    try:
        # Check specific columns generated by ta-lib wrappers
        # Column names usually: CDL_DOJI_10_0.1, CDL_ENGULFING_10_0.1 etc
        # We search for any non-zero value in CDL_* columns
        cdl_cols = [c for c in df.columns if c.startswith('CDL_')]
        found_patterns = []
        for c in cdl_cols:
            if latest[c] != 0:
                # Cleanup name: CDL_DOJI_10_0.1 -> Doji
                pat_name = c.split('_')[1].title()
                found_patterns.append(pat_name)
        
        if found_patterns:
            candle_note = ", ".join(found_patterns)
    except:
        pass

    # --- MAJOR TREND (WEEKLY) ---
    # Kept same logic as before for simplicity
    major_trend = "Netral"
    try:
        logic = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
        df_weekly = df.resample('W').apply(logic)
        df_weekly.ta.ema(length=20, append=True)
        if len(df_weekly) > 0:
            latest_weekly = df_weekly.iloc[-1]
            w_price = latest_weekly['Close']
            w_ema20 = latest_weekly.get('EMA_20', 0)
            if w_ema20 > 0:
                 if w_price > w_ema20: major_trend = "Bullish"
                 else: major_trend = "Bearish"
    except: pass

    # --- MAJOR HOLDERS ---
    major_holders = "N/A"
    try:
        t_obj = yf.Ticker(actual_ticker)
        holders = t_obj.institutional_holders
        if holders is not None and not holders.empty:
            top_holder = holders.iloc[0]['Holder']
            major_holders = f"{top_holder} (Inst)"
    except:
        major_holders = "Data Tidak Tersedia"

    # --- VALUATION (Fundamental) ---
    valuation_data = {}
    try:
        # Valuation often requires strict suffix for IDX (e.g. BBCA.JK) even if price worked for BBCA
        val_ticker = actual_ticker
        if len(actual_ticker) == 4 and not "." in actual_ticker:
             val_ticker = f"{actual_ticker}.JK"
             
        t_obj = yf.Ticker(val_ticker)
        # Use .info to fetch fundamental data
        # Note: .info can be slow or inconsistent, handle errors gracefully
        info = t_obj.info
        
        # Fallback: if val_ticker failed (empty info), try original
        if not info or len(info) < 5:
             t_obj = yf.Ticker(actual_ticker)
             info = t_obj.info
        
        pe_ratio = info.get('trailingPE', info.get('forwardPE', 0))
        pbv = info.get('priceToBook', 0)
        roe = info.get('returnOnEquity', 0)
        eps = info.get('trailingEps', info.get('forwardEps', 0))
        div_yield = info.get('dividendYield', 0)
        market_cap = info.get('marketCap', 0)
        
        # Simple Valuation Status
        val_status = "N/A"
        
        # Basic heuristic for "Undervalued"
        # PER < 15 and PBV < 1.5 is often considered "cheap" but sector dependent
        # High ROE (> 15%) is good quality
        
        if pe_ratio > 0:
            if pe_ratio < 10 and pbv < 1:
                val_status = "Undervalued (Cheap)"
            elif pe_ratio > 25 or pbv > 4:
                val_status = "Overvalued (Expensive)"
            else:
                val_status = "Fair Value"
                
        valuation_data = {
            "per": pe_ratio,
            "pbv": pbv,
            "roe": roe,
            "eps": eps,
            "dividend_yield": div_yield,
            "market_cap": market_cap,
            "valuation_status": val_status
        }
        
    except Exception as e:
        print(f"Warning: Valuation fetch failed: {e}")
        valuation_data = {
            "per": 0, "pbv": 0, "roe": 0, 
            "eps": 0, "dividend_yield": 0, 
            "market_cap": 0, "valuation_status": "N/A"
        }

    # --- SUPPORT & RESISTANCE ---
    recent_high = df['High'].tail(20).max()
    recent_low = df['Low'].tail(20).min()
    
    # --- STOP LOSS & TARGET (ATR BASED) ---
    # Dynamic SL based on volatility
    stop_loss = price - (2.0 * atr)
    target = price + (3.0 * atr)
    
    # --- CONFIDENCE SCORE & VERDICT ---
    # We calculate a confidence score (0-100) based on available proxies
    # Since we don't have real Broker/Foreign data yet, we use Proxy Bandarmology
    
    # --- RECALCULATE FIBONACCI (Required for Return) ---
    lookback = 120
    fib_slice = df.tail(lookback) if len(df) > lookback else df
    fib_high = fib_slice['High'].max()
    fib_low = fib_slice['Low'].min()
    fib_diff = fib_high - fib_low
    fib_levels = {
        0.0: fib_low, 0.236: fib_low + (0.236*fib_diff), 0.382: fib_low + (0.382*fib_diff),
        0.5: fib_low + (0.5*fib_diff), 0.618: fib_low + (0.618*fib_diff),
        0.786: fib_low + (0.786*fib_diff), 1.0: fib_high
    }
    
    # 1. Technical Score (40%)
    tech_score = 50
    if "Bullish" in trend: tech_score += 20
    elif "Bearish" in trend: tech_score -= 20
    if "Golden Cross" in macd_status: tech_score += 10
    elif "Dead Cross" in macd_status: tech_score -= 10
    if rsi > 50: tech_score += 5
    if adx > 25: tech_score += 5 # Trend strength bonus

    # 2. Bandar/Volume Score (40%)
    bandar_score = 50
    if "AKUMULASI" in sm_status: bandar_score += 30
    elif "DISTRIBUSI" in sm_status: bandar_score -= 30
    if vol_ratio > 1.5: bandar_score += 10
    if mfi > 50 and obv > obv_ema: bandar_score += 10

    # 3. Sentiment/Others (20%) - Default Neutral until AI updates it
    sentiment_score = 50 
    
    # Final Calculation
    final_score = (tech_score * 0.4) + (bandar_score * 0.4) + (sentiment_score * 0.2)
    final_score = min(100, max(0, int(final_score)))
    
    verdict = "WAIT & SEE"
    if final_score >= 75: verdict = "STRONG BUY"
    elif final_score >= 60: verdict = "BUY / ACCUMULATE"
    elif final_score <= 30: verdict = "STRONG SELL"
    elif final_score <= 45: verdict = "SELL / AVOID"

    return {
        "ticker": actual_ticker,
        "df_daily": df,
        "price": price,
        "trend": trend,
        "major_trend": major_trend,
        "rsi": rsi,
        "cci": cci,
        "adx": adx,
        "atr": atr,
        "mfi": mfi,
        "obv": obv,
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "candle_pattern": candle_note,
        "fib_levels": fib_levels,
        "volume": volume,
        "avg_volume": avg_vol_20,
        "vol_status": vol_status,
        "vol_ratio": vol_ratio,
        "bandar_status": sm_status,
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
        "target": target,
        "final_score": final_score,
        "verdict": verdict,
        "valuation": valuation_data
    }
