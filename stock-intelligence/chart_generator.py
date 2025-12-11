import mplfinance as mpf
import pandas as pd
import os
import matplotlib

# Fix threading issue on Windows
matplotlib.use('Agg')

def generate_chart(ticker, df):
    """
    Generates a complex multi-panel chart (MACD, Price+SMA+Fib, RSI, CCI).
    Saves to 'charts/{ticker}.png'.
    Returns the absolute path to the image.
    """
    try:
        print(f"Generating complex chart for {ticker}...")
    except:
        pass
    
    # Ensure charts directory exists
    charts_dir = os.path.join(os.path.dirname(__file__), "charts")
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)
        
    save_path = os.path.join(charts_dir, f"{ticker}_chart.png")
    
    # Slice last 120 days (approx 6 months) for clarity
    df_slice = df.tail(120)
    
    # --- PREPARE DATA ---
    # We need to ensure all indicators are in df_slice. 
    # Since df passed already has them calculated by technical_analysis.py, we just check existence.
    
    plots = []
    
    # 1. SMAs (Overlay on Price)
    if 'SMA_5' in df_slice.columns:
        plots.append(mpf.make_addplot(df_slice['SMA_5'], color='magenta', width=1.0, panel=0))
    if 'SMA_8' in df_slice.columns:
        plots.append(mpf.make_addplot(df_slice['SMA_8'], color='blue', width=1.0, panel=0))
    if 'SMA_13' in df_slice.columns:
        plots.append(mpf.make_addplot(df_slice['SMA_13'], color='red', width=1.0, panel=0))

    # 2. MACD (Top Panel? Or Bottom? User img had MACD top. mplfinance main panel is usually 0. 
    # Let's make Main Price = Panel 1. MACD = Panel 0. RSI = Panel 2. CCI = Panel 3.)
    
    # MACD Logic: needs macd, signal, hist columns
    # pandas_ta names: MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9
    # We search dynamically like we did for BB
    macd_col = next((c for c in df_slice.columns if c.startswith('MACD_')), None)
    signal_col = next((c for c in df_slice.columns if c.startswith('MACDs_')), None)
    hist_col = next((c for c in df_slice.columns if c.startswith('MACDh_')), None)
    
    if macd_col and signal_col and hist_col:
        plots.append(mpf.make_addplot(df_slice[macd_col], panel=2, color='blue', width=1, ylabel='MACD')) # Let's put MACD below Price for standard read
        plots.append(mpf.make_addplot(df_slice[signal_col], panel=2, color='orange', width=1))
        plots.append(mpf.make_addplot(df_slice[hist_col], panel=2, type='bar', color='dimgray', alpha=0.5))

    # 3. RSI (Panel 3)
    if 'RSI_14' in df_slice.columns:
        plots.append(mpf.make_addplot(df_slice['RSI_14'], panel=3, color='purple', ylabel='RSI', ylim=(0, 100)))
        # Add 30/70 lines manually? mpf doesn't support easy hlines in addplot, 
        # but we can do it via `fill_between` logic if needed, or just keep simple.

    # 4. CCI (Panel 4)
    # Search for CCI column (usually CCI_20_0.015)
    cci_col = next((c for c in df_slice.columns if c.startswith('CCI_')), None)
    if cci_col:
        plots.append(mpf.make_addplot(df_slice[cci_col], panel=4, color='brown', ylabel='CCI'))

    # --- FIBONACCI LINES ---
    # We calculate them again here for the slice, or use the ones passed? 
    # Ideally technical_analysis.py passed them, but we only received `df` in this function.
    # We'll re-calc quick max/min on the slice to be accurate to what's shown.
    
    fib_high = df_slice['High'].max()
    fib_low = df_slice['Low'].min()
    fib_diff = fib_high - fib_low
    
    hlines = []
    colors = []
    
    if fib_diff > 0:
        levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        # Colors: 0 & 1 red, others various
        for level in levels:
            price_level = fib_low + (level * fib_diff)
            hlines.append(price_level)
            if level in [0.0, 1.0]:
                colors.append('red')
            elif level == 0.5:
                colors.append('orange')
            else:
                colors.append('green')

    # Prepare Style
    # User wanted "like that" -> The image usually has a white/light background.
    # Let's try 'yahoo' style which is light and standard.
    s = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'figure.facecolor': 'lightgray'})

    try:
        mpf.plot(
            df_slice,
            type='candle',
            style=s,
            title=f"{ticker} Daily (Fib+SMA+MACD+RSI+CCI)",
            ylabel='Price (IDR)',
            volume=True,
            volume_panel=1, # Volume below price
            addplot=plots,
            hlines=dict(hlines=hlines, colors=colors, linewidths=0.5, alpha=0.8),
            panel_ratios=(4, 1, 1.5, 1.5, 1.5), # Price=4, Vol=1, MACD=1.5, RSI=1.5, CCI=1.5
            savefig=dict(fname=save_path, dpi=100, bbox_inches='tight'),
            tight_layout=True
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
    # Test requires a dataframe, skipping auto-run
    pass
