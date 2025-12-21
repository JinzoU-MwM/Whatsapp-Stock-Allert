import mplfinance as mpf
import pandas as pd
import os
import matplotlib

# Fix threading issue on Windows
matplotlib.use('Agg')

def generate_chart(ticker, df, broker_history_df=None, broker_flow_df=None, chart_mode='technical'):
    """
    Generates a professional candlestick chart (TradingView style) using mplfinance.
    modes: 'technical' (Standard), 'bandarmology' (Focus on Broker Flow)
    """
    try:
        print(f"Generating chart for {ticker} (Mode: {chart_mode})...")
    except:
        pass
    
    # Ensure charts directory exists
    charts_dir = os.path.join(os.path.dirname(__file__), "charts")
    if not os.path.exists(charts_dir):
        os.makedirs(charts_dir)
        
    save_path = os.path.join(charts_dir, f"{ticker}_{chart_mode}_chart.png")
    
    # Slice last 100 periods for optimal viewing
    df_slice = df.tail(100).copy()
    
    # --- PREPARE PLOTS ---
    plots = []
    
    # Default Config (Technical)
    panel_price = 0
    panel_vol = 1
    current_panel = 2
    panels_ratios_list = [4, 1] 
    show_volume = True
    
    if chart_mode == 'bandarmology':
        # SPECIAL LAYOUT: PRICE + BROKER FLOW ONLY
        # Panel 0: Price (Clean, no EMAs usually, or maybe just basic)
        # Panel 1: Broker Flow
        panel_vol = None # Disable Volume Panel
        current_panel = 1 
        panels_ratios_list = [4, 2] # Price(4) : Flow(2)
        show_volume = False
        
    else:
        # TECHNICAL MODE (Standard)
        # 1. EMAs (Standard Overlay)
        if 'EMA_20' in df_slice.columns:
            plots.append(mpf.make_addplot(df_slice['EMA_20'], color='blue', width=1.0, panel=panel_price))
        if 'EMA_50' in df_slice.columns:
            plots.append(mpf.make_addplot(df_slice['EMA_50'], color='orange', width=1.0, panel=panel_price))
        if 'EMA_200' in df_slice.columns:
            if df_slice['EMA_200'].notna().sum() > 0:
                 plots.append(mpf.make_addplot(df_slice['EMA_200'], color='red', width=1.5, panel=panel_price))
                 
        # 2. Bollinger Bands
        bbu_col = next((c for c in df_slice.columns if c.startswith('BBU_')), None)
        bbl_col = next((c for c in df_slice.columns if c.startswith('BBL_')), None)
        if bbu_col and bbl_col:
             plots.append(mpf.make_addplot(df_slice[bbu_col], color='gray', alpha=0.3, width=0.8, panel=panel_price))
             plots.append(mpf.make_addplot(df_slice[bbl_col], color='gray', alpha=0.3, width=0.8, panel=panel_price))

    # --- MODE SPECIFIC PANELS ---
    
    if chart_mode == 'technical':
        # Standard MACD & RSI
        macd_col = next((c for c in df_slice.columns if c.startswith('MACD_')), None)
        signal_col = next((c for c in df_slice.columns if c.startswith('MACDs_')), None)
        hist_col = next((c for c in df_slice.columns if c.startswith('MACDh_')), None)
        
        if macd_col and signal_col and hist_col:
            plots.append(mpf.make_addplot(df_slice[macd_col], panel=current_panel, color='blue', width=1.0, ylabel='MACD'))
            plots.append(mpf.make_addplot(df_slice[signal_col], panel=current_panel, color='orange', width=1.0))
            hist_colors = ['green' if v >= 0 else 'red' for v in df_slice[hist_col]]
            plots.append(mpf.make_addplot(df_slice[hist_col], panel=current_panel, type='bar', color=hist_colors, alpha=0.5))
            panels_ratios_list.append(1.5)
            current_panel += 1

        if 'RSI_14' in df_slice.columns:
            plots.append(mpf.make_addplot(df_slice['RSI_14'], panel=current_panel, color='purple', ylabel='RSI', ylim=(10, 90)))
            panels_ratios_list.append(1.5)
            current_panel += 1
            
    elif chart_mode == 'bandarmology':
        # BROKER FLOW CHART (Multi-Line, Panel 1)
        if broker_flow_df is not None and not broker_flow_df.empty:
            broker_flow_df.index = pd.to_datetime(broker_flow_df.index)
            aligned_flow = broker_flow_df.reindex(df_slice.index)
            aligned_flow = aligned_flow.fillna(method='ffill')
            
            # Distinct colors
            colors = ['#2980b9', '#e74c3c', '#27ae60', '#f39c12', '#8e44ad', '#16a085']
            
            for i, col in enumerate(aligned_flow.columns):
                c = colors[i % len(colors)]
                plots.append(mpf.make_addplot(
                    aligned_flow[col],
                    panel=current_panel, # Panel 1
                    color=c,
                    width=2.0,
                    ylabel='Broker Flow' if i == 0 else '' 
                ))
            
            # No update to current_panel needed as it's the last one
            
        elif broker_history_df is not None:
             # Fallback Bar Chart
            broker_history_df.index = pd.to_datetime(broker_history_df.index)
            aligned_broker = broker_history_df.reindex(df_slice.index)
            aligned_broker['NetTop3Vol'] = aligned_broker['NetTop3Vol'].fillna(0)
            broker_colors = ['#00ff00' if v >= 0 else '#ff0000' for v in aligned_broker['NetTop3Vol']]
            
            plots.append(mpf.make_addplot(
                aligned_broker['NetTop3Vol'], 
                panel=current_panel, 
                type='bar', 
                color=broker_colors, 
                alpha=0.6,
                ylabel='Bandar Vol'
            ))

    # --- STYLE & PLOT ---
    market_colors = mpf.make_marketcolors(
        up='#00ff00', down='#ff0000',
        edge='inherit',
        wick='inherit',
        volume={'up': '#00ff00', 'down': '#ff0000'},
        ohlc='inherit'
    )
    
    s = mpf.make_mpf_style(
        base_mpf_style='nightclouds', 
        marketcolors=market_colors,
        gridstyle=':', 
        y_on_right=True
    )

    try:
        mpf.plot(
            df_slice,
            type='candle',
            style=s,
            title=f"{ticker} ({chart_mode.title()})",
            ylabel='Price',
            ylabel_lower='Volume',
            volume=show_volume,
            addplot=plots,
            panel_ratios=tuple(panels_ratios_list), 
            savefig=dict(fname=save_path, dpi=120, bbox_inches='tight', pad_inches=0.2),
            tight_layout=True,
            scale_width_adjustment=dict(candle=1.1, volume=0.7)
        )
        return os.path.abspath(save_path)
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None

if __name__ == "__main__":
    pass
