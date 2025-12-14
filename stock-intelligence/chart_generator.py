import mplfinance as mpf
import pandas as pd
import os
import matplotlib

# Fix threading issue on Windows
matplotlib.use('Agg')

def generate_chart(ticker, df):
    """
    Generates a professional candlestick chart (TradingView style) using mplfinance.
    Includes:
    - Candlestick Price
    - Volume
    - Moving Averages (EMA 20, 50, 200)
    - MACD (Bottom Panel)
    - RSI (Top Panel or separate)
    Saves to 'charts/{ticker}_chart.png'.
    Returns the absolute path to the image.
    """
    try:
        print(f"Generating professional chart for {ticker}...")
    except:
        pass
    
    # Ensure charts directory exists
    charts_dir = os.path.join(os.path.dirname(__file__), "charts")
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)
        
    save_path = os.path.join(charts_dir, f"{ticker}_chart.png")
    
    # Slice last 100 periods for optimal viewing
    df_slice = df.tail(100).copy() # Use copy to avoid settingwithcopy warning
    
    # --- PREPARE PLOTS ---
    plots = []
    
    # 1. EMAs (Overlay on Price) - Calculate if missing or just use columns
    # We prefer calculating fresh for the plot to be safe, or reusing DF columns
    # Re-calculating using pandas_ta logic if not present, but technical_analysis usually adds them.
    # We will strictly look for columns.
    
    if 'EMA_20' in df_slice.columns:
        plots.append(mpf.make_addplot(df_slice['EMA_20'], color='blue', width=1.0, panel=0))
    if 'EMA_50' in df_slice.columns:
        plots.append(mpf.make_addplot(df_slice['EMA_50'], color='orange', width=1.0, panel=0))
    if 'EMA_200' in df_slice.columns:
        # Check if 200 EMA has valid values in the slice
        if df_slice['EMA_200'].notna().sum() > 0:
             plots.append(mpf.make_addplot(df_slice['EMA_200'], color='red', width=1.5, panel=0))
             
    # 2. Bollinger Bands
    # Look for BBU/BBL columns
    bbu_col = next((c for c in df_slice.columns if c.startswith('BBU_')), None)
    bbl_col = next((c for c in df_slice.columns if c.startswith('BBL_')), None)
    if bbu_col and bbl_col:
         plots.append(mpf.make_addplot(df_slice[bbu_col], color='gray', alpha=0.3, width=0.8, panel=0))
         plots.append(mpf.make_addplot(df_slice[bbl_col], color='gray', alpha=0.3, width=0.8, panel=0))
         # Fill between is complex in addplot, simple lines are fine for now or mpf native 'mav' logic

    # 3. MACD (Panel 2 - Bottom)
    # Using columns from technical_analysis.py
    macd_col = next((c for c in df_slice.columns if c.startswith('MACD_')), None)
    signal_col = next((c for c in df_slice.columns if c.startswith('MACDs_')), None)
    hist_col = next((c for c in df_slice.columns if c.startswith('MACDh_')), None)
    
    if macd_col and signal_col and hist_col:
        plots.append(mpf.make_addplot(df_slice[macd_col], panel=2, color='blue', width=1.0, ylabel='MACD'))
        plots.append(mpf.make_addplot(df_slice[signal_col], panel=2, color='orange', width=1.0))
        # Histogram color logic
        hist_colors = ['green' if v >= 0 else 'red' for v in df_slice[hist_col]]
        plots.append(mpf.make_addplot(df_slice[hist_col], panel=2, type='bar', color=hist_colors, alpha=0.5))

    # 4. RSI (Panel 1 - Middle, replacing Volume which is usually usually integrated or Panel 1)
    # Let's put Volume on Panel 1, MACD on Panel 2. 
    # Wait, mpf puts Volume on Panel 1 by default if volume=True.
    # So Price=0, Volume=1.
    # Let's put MACD on Panel 2.
    # Let's put RSI on Panel 3.
    
    if 'RSI_14' in df_slice.columns:
        plots.append(mpf.make_addplot(df_slice['RSI_14'], panel=3, color='purple', ylabel='RSI', ylim=(10, 90)))
        # Add 30/70 reference lines? mpf hlines param applies to main plot usually, difficult for subpanels.
        # We'll skip lines for now to keep it clean.

    # --- STYLE & PLOT ---
    # Custom style for "Pro" look
    market_colors = mpf.make_marketcolors(
        up='#00ff00', down='#ff0000',
        edge='inherit',
        wick='inherit',
        volume={'up': '#00ff00', 'down': '#ff0000'},
        ohlc='inherit'
    )
    
    s = mpf.make_mpf_style(
        base_mpf_style='nightclouds', # Dark theme professional
        marketcolors=market_colors,
        gridstyle=':', 
        y_on_right=True
    )

    try:
        mpf.plot(
            df_slice,
            type='candle',
            style=s,
            title=f"\n{ticker} Professional Chart",
            ylabel='Price',
            ylabel_lower='Volume',
            volume=True,
            addplot=plots,
            panel_ratios=(4, 1, 1.5, 1.5), # Price, Vol, MACD, RSI
            savefig=dict(fname=save_path, dpi=120, bbox_inches='tight', pad_inches=0.2),
            tight_layout=True,
            scale_width_adjustment=dict(candle=1.1, volume=0.7)
        )
        try:
            print(f"Chart saved to {save_path}")
        except:
            pass
        return os.path.abspath(save_path)
    except Exception as e:
        try:
            print(f"Error generating chart: {e}")
        except:
            pass
        return None

if __name__ == "__main__":
    pass
