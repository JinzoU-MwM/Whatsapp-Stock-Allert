import mplfinance as mpf
import pandas as pd
import os

def generate_chart(ticker, df):
    """
    Generates a candlestick chart with EMA 20 & 50.
    Saves to 'charts/{ticker}.png'.
    Returns the absolute path to the image.
    """
    print(f"🎨 Generating chart for {ticker}...")
    
    # Ensure charts directory exists
    charts_dir = os.path.join(os.path.dirname(__file__), "charts")
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)
        
    save_path = os.path.join(charts_dir, f"{ticker}_chart.png")
    
    # Prepare Style
    # Classic dark theme with clear candles
    mc = mpf.make_marketcolors(up='#00ff00', down='#ff0000', inherit=True)
    s  = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)
    
    # Add Plots (EMAs)
    # Ensure EMA columns exist, or calculate them if missing from df view
    # In technical_analysis.py we appended them.
    # Note: df passed here should have the EMA columns ready.
    
    addplots = []
    if 'EMA_20' in df.columns:
        addplots.append(mpf.make_addplot(df['EMA_20'], color='yellow', width=1.5))
    if 'EMA_50' in df.columns:
        addplots.append(mpf.make_addplot(df['EMA_50'], color='cyan', width=1.5))
        
    # We slice last 6 months (approx 120 candles) for clarity
    df_slice = df.tail(120)
    
    try:
        mpf.plot(
            df_slice,
            type='candle',
            style=s,
            title=f"{ticker} Daily Chart",
            ylabel='Price (IDR)',
            volume=True,
            addplot=[p for p in addplots if len(p['data']) == len(df_slice)], # Match length
            savefig=dict(fname=save_path, dpi=100, bbox_inches='tight'),
            tight_layout=True
        )
        print(f"✅ Chart saved to {save_path}")
        return os.path.abspath(save_path)
    except Exception as e:
        print(f"❌ Error generating chart: {e}")
        return None

if __name__ == "__main__":
    # Test requires a dataframe, skipping auto-run
    pass
