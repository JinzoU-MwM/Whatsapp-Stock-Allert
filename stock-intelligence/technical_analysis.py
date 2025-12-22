import pandas as pd
import numpy as np
import os
import datetime
# LAZY IMPORTS: yfinance and pandas_ta are imported inside functions to speed up app launch
# import yfinance as yf
# import pandas_ta as ta

try:
    from goapi_client import GoApiClient
except ImportError:
    GoApiClient = None

def get_stock_data(ticker, period="2y", interval="1d"):
    """
    Fetches stock data.
    Strictly prioritizes IDX (.JK) for 4-letter tickers to avoid US stock collisions.
    """
    import yfinance as yf # Lazy import
    
    print(f"Fetching data for {ticker}...")
    
    df = pd.DataFrame()
    actual_ticker = ticker
    
    # Logic: If ticker is 4 letters and no dot, try .JK FIRST.
    # This prevents getting US data for 'COAL', 'ABBA', 'FREN' etc.
    tickers_to_try = []
    if len(ticker) == 4 and "." not in ticker:
        tickers_to_try.append(f"{ticker}.JK")
    tickers_to_try.append(ticker)
    
    # Try fetching
    for t in tickers_to_try:
        try:
            print(f"   [Source] Attempting yfinance for {t}...")
            # Use auto_adjust=True for better price continuity (splits/dividends)
            temp_df = yf.download(t, period=period, interval=interval, progress=False, auto_adjust=True)
            
            # Check for MultiIndex columns (yfinance > 0.2.0)
            if isinstance(temp_df.columns, pd.MultiIndex):
                temp_df.columns = temp_df.columns.get_level_values(0)
            
            if not temp_df.empty:
                # Basic validation: Check if recent volume is not zero (delisted/inactive check)
                if temp_df['Volume'].tail(5).sum() > 0:
                    df = temp_df
                    actual_ticker = t
                    print(f"   [Source] Success with {t}")
                    break
        except Exception as e:
            print(f"   [Source] Failed for {t}: {e}")

    if df.empty:
        raise ValueError(f"No valid data found for ticker {ticker}. Ensure it is an active IDX stock.")

    return df, actual_ticker

def get_valuation_data(ticker):
    """
    Fetches fundamental valuation data (PER, PBV, ROE) for a ticker.
    Fetches fundamental valuation data (PER, PBV, ROE) for a ticker.
    Handles the .JK suffix logic independently to allow parallel execution in future.
    """
    import yfinance as yf # Lazy import
    
    valuation_data = {
        "per": 0, "pbv": 0, "roe": 0, 
        "eps": 0, "dividend_yield": 0, 
        "market_cap": 0, "valuation_status": "N/A"
    }
    
    import os
    goapi_key = os.getenv("GOAPI_API_KEY")
    
    # 1. Try GoAPI First (If Available)
    if goapi_key:
        try:
            from goapi_client import GoApiClient
            client = GoApiClient(goapi_key)
            profile = client.get_profile(ticker)
            
            if profile:
                print(f"   [Valuation] Using GoAPI Data for {ticker}")
                # Map GoAPI fields to our structure
                # GoAPI fields: 'per', 'pbv', 'roe', 'eps', 'market_cap'
                valuation_data['per'] = float(profile.get('per', 0) or 0)
                valuation_data['pbv'] = float(profile.get('pbv', 0) or 0)
                valuation_data['roe'] = float(profile.get('roe', 0) or 0)
                valuation_data['eps'] = float(profile.get('eps_ttm', 0) or profile.get('eps', 0) or 0)
                valuation_data['market_cap'] = float(profile.get('market_cap', 0) or 0)
                valuation_data['valuation_status'] = _determine_valuation_status(valuation_data['per'], valuation_data['pbv'])
                
                # Close gap with other logic
                return valuation_data
        except Exception as e:
            print(f"   [Valuation] GoAPI Failed: {e}, falling back to YFinance")

    try:
        # Valuation often requires strict suffix for IDX (e.g. BBCA.JK)
        val_tickers_to_try = []
        if len(ticker) == 4 and not "." in ticker:
             val_tickers_to_try.append(f"{ticker}.JK")
        val_tickers_to_try.append(ticker)
        
        info = None
        for t in val_tickers_to_try:
            try:
                t_obj = yf.Ticker(t)
                temp_info = t_obj.info
                # Check if valid data received (Yahoo sometimes returns empty dict or generic metadata)
                if temp_info and len(temp_info) > 5 and 'regularMarketPrice' in temp_info:
                    info = temp_info
                    print(f"   [Valuation] Success with {t}")
                    break
            except Exception:
                continue
        
        if not info:
            # If all failed, use the last one just to have something, or keep empty
            print(f"   [Valuation] Warning: No fundamental data found for {ticker}")
            return valuation_data
        
        # Extract Data with Fallbacks
        current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        eps = info.get('trailingEps', info.get('forwardEps', 0))
        
        # 1. Try standard fields
        pe_ratio = info.get('trailingPE', info.get('forwardPE'))
        
        # 2. Fallback: Calculate manually if PE is None but we have Price & EPS (handles negative earnings)
        if pe_ratio is None and current_price and eps and eps != 0:
            pe_ratio = current_price / eps
            
        # 3. Final default to 0 if still None
        if pe_ratio is None:
            pe_ratio = 0

        pbv = info.get('priceToBook', 0)
        roe = info.get('returnOnEquity', 0)
        div_yield = info.get('dividendYield', 0)
        market_cap = info.get('marketCap', 0)
        # New Metrics for Fundamental Agent
        der = info.get('debtToEquity', 0)
        eps_growth = info.get('earningsGrowth', 0) # This is usually decimal (0.15 for 15%)
        if eps_growth: eps_growth = eps_growth * 100 # Convert to %
        
        currency = info.get('currency', 'IDR')
        fin_currency = info.get('financialCurrency', currency) # Default to same if missing
        
        # FORCE IDR CONVERSION
        # Logic: If currency is USD, multiply by ~16000 (Conservative Rate)
        usd_idr_rate = 16200 
        
        # Case A: Market Cap / Quote is in USD (Rare for .JK, but possible)
        if currency == 'USD':
            print(f"   [Valuation] Detected USD Quote for {ticker}. Converting to IDR...")
            market_cap = market_cap * usd_idr_rate
            eps = eps * usd_idr_rate
            
        # Case B: Quote in IDR, but Financials (Book Value) in USD (Common for Energy/Mining like ADRO, ITMG)
        if fin_currency == 'USD' and currency == 'IDR':
             if pbv > 100: 
                 print(f"   [Valuation] Detected IDR/USD Mismatch for {ticker} (PBV {pbv:.0f}x). Adjusting...")
                 pbv = pbv / usd_idr_rate
        
        # Refined Valuation Logic
        val_status = "N/A"
        if pe_ratio > 0 or pbv > 0:
            if (0 < pe_ratio < 10) and (0 < pbv < 1):
                val_status = "Undervalued (Cheap)"
            elif pe_ratio > 25 or pbv > 4:
                val_status = "Overvalued (Expensive)"
            elif pe_ratio == 0 and pbv > 0:
                val_status = "Negative Earnings"
            else:
                val_status = "Fair Value"
                
        valuation_data = {
            "per": pe_ratio,
            "pbv": pbv,
            "roe": roe,
            "eps": eps,
            "der": der,
            "eps_growth": eps_growth,
            "dividend_yield": div_yield,
            "market_cap": market_cap,
            "valuation_status": val_status,
            "currency": "IDR" 
        }
    except Exception as e:
        print(f"Warning: Valuation fetch failed: {e}")
        
    return valuation_data

import concurrent.futures

def analyze_technical(ticker, timeframe="daily"):
    """
    Performs technical analysis using pandas_ta.
    Returns a dictionary with trend, support, resistance, key levels, VOLUME ANALYSIS, AND BANDARMOLOGY.
    EXPERIMENTAL: Parallel Execution for Speed
    """
    import pandas_ta as ta # Lazy Import to register .ta accessor
    
    # Helper to clean up code
    def fetch_price():
        if timeframe == "weekly":
            return get_stock_data(ticker, period="2y", interval="1wk")
        elif timeframe == "monthly":
            return get_stock_data(ticker, period="5y", interval="1mo")
        else:
            return get_stock_data(ticker, period="1y", interval="1d")

    # Parallel Fetching: Price & Valuation are independent
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_price = executor.submit(fetch_price)
        future_val = executor.submit(get_valuation_data, ticker) # Check ticker suffix handling inside
        
        # We need Actual Ticker from price fetch for some logic, but valuation handles its own
        try:
            df, actual_ticker = future_price.result()
        except Exception as e:
            # If price fails, we can't do much
            raise e
            
        valuation_data = future_val.result()

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
    df.ta.vwap(append=True) # Returns VWAP_D (Volume Weighted Average Price)
    
    # Calculate OBV EMA for trend signal
    
    # ... [After processing df] ...
    
    # Extract Latest Values
    latest = df.iloc[-1]
    
    # Price Change
    try:
        if len(df) > 1:
            prev_close = df.iloc[-2]['Close']
            curr_close = latest['Close']
            change_pct = ((curr_close - prev_close) / prev_close) * 100
        else:
            change_pct = 0
    except:
        change_pct = 0
        
    vwap_val = latest.get('VWAP_D', 0)
    if pd.isna(vwap_val): vwap_val = 0
    
    # (Removed premature result block)
    # We need to explicitly access the OBV column since column name is just 'OBV'
    if 'OBV' in df.columns:
        df['OBV_EMA'] = ta.ema(df['OBV'], length=20)
    
    # 5. MACD & Bollinger Bands
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    
    # 6. Candlestick Patterns
    # Note: shooting_star might not be available in base pandas_ta without ta-lib
    patterns = ["doji", "engulfing", "hammer"]
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
    valuation_data = get_valuation_data(actual_ticker)

    # --- PIVOT POINTS (Standard) ---
    # Pivot = (High + Low + Close) / 3
    # R1 = 2*P - Low, S1 = 2*P - High
    # R2 = P + (High - Low), S2 = P - (High - Low)
    
    pivots = {}
    try:
        p_high = float(latest['High'])
        p_low = float(latest['Low'])
        p_close = float(latest['Close'])
        
        pp = (p_high + p_low + p_close) / 3
        r1 = (2 * pp) - p_low
        s1 = (2 * pp) - p_high
        r2 = pp + (p_high - p_low)
        s2 = pp - (p_high - p_low)
        
        pivots = {
            "pivot": pp,
            "r1": r1, "s1": s1,
            "r2": r2, "s2": s2
        }
    except Exception as e:
        print(f"Pivot Calc Error: {e}")

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
    
    # --- RECENT HISTORY (For AI Context) ---
    history_str = "Date | Close | Vol | Change%\n"
    try:
        last_5 = df.tail(5)
        for date, row in last_5.iterrows():
            d_str = date.strftime('%Y-%m-%d')
            c_price = row['Close']
            vol = row['Volume']
            
            # Calc change if possible
            # Need prev close, but row doesn't have it easily unless we shift.
            # Approximation: current/prev - 1. 
            # Easier: Just basic data.
            history_str += f"{d_str} | {c_price:.0f} | {vol/1000:.0f}k\n"
    except:
        history_str = "Data History N/A"

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
        "vwap": vwap_val,
        "change_pct": change_pct,
        "final_score": final_score,
        "verdict": verdict,
        "valuation": valuation_data,
        "recent_history": history_str,
        "pivots": pivots
    }
