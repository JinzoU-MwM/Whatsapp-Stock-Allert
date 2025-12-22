import pandas as pd
import numpy as np
try:
    from goapi_client import GoApiClient
except ImportError:
    GoApiClient = None

class QuantAnalyzer:
    def __init__(self, goapi_client=None):
        self.goapi_client = goapi_client
        # Daftar Broker Retail (Contoh)
        self.retail_brokers = ['YP', 'PD', 'CC', 'NI', 'XC', 'XL', 'KK']
        # Daftar Broker Institusi/Asing (Contoh)
        self.insti_brokers = ['BK', 'ZP', 'AK', 'KZ', 'RX', 'CS', 'CG']

    def fetch_real_bandarmology(self, ticker):
        """
        Fetches and analyzes real Broker Summary and Foreign Flow from GoAPI if available.
        Returns a combined dictionary of scores and status.
        """
        if not self.goapi_client or not self.goapi_client.check_connection():
            return None

        print(f"   [Quant] Fetching Real Bandarmology Data for {ticker} from GoAPI...")
        
        # 1. Broker Summary
        broker_data = self.goapi_client.get_broker_summary(ticker)
        bs_result = self._process_goapi_broker_data(broker_data)
        
        # 2. Foreign Flow
        foreign_data = self.goapi_client.get_foreign_flow(ticker)
        ff_result = self._process_goapi_foreign_data(foreign_data)
        
        return {
            "broker_summary": bs_result,
            "foreign_flow": ff_result
        }

    def _process_goapi_broker_data(self, data):
        """Parses GoAPI broker summary response into analysis format."""
        if not data:
            return {"status": "Neutral", "score": 0, "summary": "Data Broker N/A"}
            
        # Expecting list of dicts: [{'code': 'YP', 'side': 'BUY', 'lot': 100, 'value': 1000, 'avg': 1000}, ...]
        # Transform to DataFrame for analyze_broker_summary
        rows = []
        for item in data:
            code = item.get('broker_code') or item.get('code')
            side = item.get('side', '').upper()
            val = float(item.get('value', 0) or item.get('lot', 0)) # Prefer value, fallback to lot if needed
            avg = float(item.get('avg', 0))
            
            # GoAPI returns row-based (one row for BUY, one for SELL per broker)
            if side == 'BUY':
                rows.append({'Broker': code, 'Action': 'BUY', 'Volume': val, 'AvgPrice': avg})
            elif side == 'SELL':
                rows.append({'Broker': code, 'Action': 'SELL', 'Volume': val, 'AvgPrice': avg})
            # Handle legacy format where buy_vol and sell_vol are in one row (if API changes back)
            elif 'buy_vol' in item:
                b_vol = float(item.get('buy_vol', 0))
                s_vol = float(item.get('sell_vol', 0))
                if b_vol > 0: rows.append({'Broker': code, 'Action': 'BUY', 'Volume': b_vol, 'AvgPrice': float(item.get('buy_avg',0))})
                if s_vol > 0: rows.append({'Broker': code, 'Action': 'SELL', 'Volume': s_vol, 'AvgPrice': float(item.get('sell_avg',0))})
                
        if not rows:
            return {"status": "Neutral", "score": 0, "summary": "Data Broker Kosong"}
            
        df = pd.DataFrame(rows)
        return self.analyze_broker_summary(df)

    def _process_goapi_foreign_data(self, data):
        """Parses GoAPI foreign flow response."""
        if not data:
            return {"status": "Unknown", "score": 0}
            
        # Expecting list: [{'date': '...', 'net_buy': ...}, ...]
        # We need a DataFrame with 'NetForeignBuy' column
        rows = []
        for item in data:
            # Try multiple keys for robustness (GoAPI response vary)
            net = float(
                item.get('net_foreign_buy') or 
                item.get('net_buy') or 
                item.get('foreign_net_buy') or
                item.get('net_foreign_val') or # Value based
                item.get('net_foreign_vol') or # Volume based
                item.get('net_buy_foreign_val') or
                0
            )
            date = item.get('date') or item.get('datetime')
            rows.append({'Date': date, 'NetForeignBuy': net})
            
        if not rows:
            return {"status": "Unknown", "score": 0}
            
        df = pd.DataFrame(rows)
        return self.analyze_foreign_flow(df)

    def analyze_broker_summary(self, transaction_data):
        """
        Menganalisis Data Transaksi Broker (Bandarmology).
        
        Param:
        transaction_data (DataFrame): Kolom ['Broker', 'Action', 'Volume', 'AvgPrice']
                                      Action: 'BUY' atau 'SELL'
        
        Output: Dictionary analisis Bandarmology.
        """
        if transaction_data is None or transaction_data.empty:
            return {
                "status": "Neutral",
                "score": 0,
                "summary": "Data Broker Tidak Tersedia",
                "top_buyer_type": "Unknown"
            }

        # 1. Grouping Data
        buys = transaction_data[transaction_data['Action'] == 'BUY'].groupby('Broker').agg(
            {'Volume': 'sum', 'AvgPrice': 'mean'}
        ).sort_values('Volume', ascending=False)
        
        sells = transaction_data[transaction_data['Action'] == 'SELL'].groupby('Broker').agg(
            {'Volume': 'sum', 'AvgPrice': 'mean'}
        ).sort_values('Volume', ascending=False)

        # 2. Top 3 Analysis
        top3_buy_vol = buys.head(3)['Volume'].sum()
        top3_sell_vol = sells.head(3)['Volume'].sum()
        
        # Get Top 3 Broker Codes
        top3_buyers = buys.head(3).index.tolist()
        top3_sellers = sells.head(3).index.tolist()
        
        top1_buyer = buys.index[0] if not buys.empty else "N/A"
        top1_seller = sells.index[0] if not sells.empty else "N/A"

        # 3. Deteksi Tipe Bandar
        buyer_type = "Retail" if top1_buyer in self.retail_brokers else "Institusi/Market Maker"
        
        # 4. Kalkulasi Kekuatan (Accumulation/Distribution)
        net_vol_ratio = 0
        if top3_sell_vol > 0:
            net_vol_ratio = top3_buy_vol / top3_sell_vol
        
        status = "Netral"
        score = 0 # Skala -50 (Distribusi Kuat) s/d +50 (Akumulasi Kuat)

        if net_vol_ratio > 1.5:
            if buyer_type == "Institusi/Market Maker":
                status = "BIG ACCUMULATION (Institusi)"
                score = 50
            else:
                status = "Akumulasi Retail (Hati-hati)"
                score = 20
        elif net_vol_ratio > 1.1:
            status = "Akumulasi Ringan"
            score = 10
        elif net_vol_ratio < 0.6:
            status = "BIG DISTRIBUTION"
            score = -50
        elif net_vol_ratio < 0.9:
            status = "Distribusi Ringan"
            score = -20
        
        # 5. Cek Average Price (Average Down/Up)
        avg_buy_price = buys.head(3)['AvgPrice'].mean()
        avg_sell_price = sells.head(3)['AvgPrice'].mean()
        avg_price_diff = avg_buy_price - avg_sell_price
        
        # Format Top 3 string
        top3_buyers_str = ",".join(top3_buyers)
        top3_sellers_str = ",".join(top3_sellers)
        
        narrative = f"{status}. Buyer Dominan: {top3_buyers_str}. Seller Dominan: {top3_sellers_str}."
        
        # Get Top 1 Prices specifically for Power Buyer Logic
        top1_buy_price = 0
        top1_sell_price = 0
        if not buys.empty:
             top1_buy_price = buys.iloc[0]['AvgPrice']
        if not sells.empty:
             top1_sell_price = sells.iloc[0]['AvgPrice']

        return {
            "status": status,
            "bandar_score": score,
            "top_buyer": top1_buyer,
            "top3_buyers": top3_buyers,
            "top_seller": top1_seller,
            "top3_sellers": top3_sellers,
            "buyer_type": buyer_type,
            "net_vol_ratio": net_vol_ratio,
            "avg_price_diff": avg_price_diff,
            "avg_buy_price": avg_buy_price, # Top 3 Mean
            "top1_buy_price": top1_buy_price, # Specific Top 1
            "top1_sell_price": top1_sell_price, # Specific Top 1
            "summary": narrative
        }

    def analyze_foreign_flow(self, foreign_data):
        """
        Analisa Aliran Dana Asing (Foreign Flow).
        
        Param:
        foreign_data (DataFrame): Index Tanggal, Kolom ['NetForeignBuy']
        """
        if foreign_data is None or foreign_data.empty:
            return {"status": "Unknown", "score": 0}

        # Cek akumulasi
        net_1d = foreign_data['NetForeignBuy'].iloc[-1]
        net_5d = foreign_data['NetForeignBuy'].tail(5).sum()
        net_20d = foreign_data['NetForeignBuy'].tail(20).sum()
        
        score = 0
        status = "Netral"
        
        if net_1d > 0 and net_5d > 0:
            status = "Foreign Inflow (Masuk)"
            score = 20
            if net_20d > 0:
                status = "Strong Foreign Accumulation"
                score = 30
        elif net_1d < 0 and net_5d < 0:
            status = "Foreign Outflow (Keluar)"
            score = -20
        
        return {
            "status": status,
            "foreign_score": score,
            "net_1d": net_1d,
            "net_5d": net_5d
        }

    def analyze_historical_broker_summary(self, historical_data):
        """
        Aggregates historical broker summary into a DataFrame for plotting.
        Param:
            historical_data (dict): {date_str: raw_broker_list} from get_broker_summary_historical
            
        Returns:
            DataFrame: Index=Date, Cols=['NetTop3Vol', 'AcumStatus']
        """
        if not historical_data:
            return None
            
        rows = []
        
        # Sort dates ascending
        sorted_dates = sorted(historical_data.keys())
        
        for d_str in sorted_dates:
            daily_raw = historical_data[d_str]
            # Convert to DF using existing logic helper
            df_daily_temp = self._process_goapi_broker_data_raw(daily_raw)
            
            if df_daily_temp is not None and not df_daily_temp.empty:
                # Calculate Net Top 3 Volume (Buy Vol - Sell Vol)
                # This is a simplified "Bandar Flow" metric.
                
                # Group by Broker
                buys = df_daily_temp[df_daily_temp['Action'] == 'BUY'].groupby('Broker')['Volume'].sum()
                sells = df_daily_temp[df_daily_temp['Action'] == 'SELL'].groupby('Broker')['Volume'].sum()
                
                # Get Top 3 Buyers & Sellers for THIS day
                top3_buyers = buys.sort_values(ascending=False).head(3).index.tolist()
                top3_sellers = sells.sort_values(ascending=False).head(3).index.tolist()
                
                # Calculate Net Volume of these Top 3 Buyers
                # (How much did the top buyers accumulated net?)
                net_vol = 0
                for b in top3_buyers:
                    b_buy = buys.get(b, 0)
                    b_sell = sells.get(b, 0)
                    net_vol += (b_buy - b_sell)
                    
                rows.append({
                    'Date': pd.to_datetime(d_str),
                    'NetTop3Vol': net_vol,
                    'Top3Buyers': ",".join(top3_buyers),
                    'Top3Sellers': ",".join(top3_sellers)
                })
                
        if not rows:
            return None
            
        df = pd.DataFrame(rows)
        df.set_index('Date', inplace=True)
        return df

    def _process_goapi_broker_data_raw(self, data):
        """Helper to convert raw list to DF without full analysis."""
        if not data: return None
        rows = []
        for item in data:
            code = item.get('broker_code') or item.get('code')
            side = item.get('side', '').upper()
            val = float(item.get('value', 0) or item.get('lot', 0))
            avg = float(item.get('avg', 0))
            
            if side == 'BUY':
                rows.append({'Broker': code, 'Action': 'BUY', 'Volume': val, 'AvgPrice': avg})
            elif side == 'SELL':
                rows.append({'Broker': code, 'Action': 'SELL', 'Volume': val, 'AvgPrice': avg})
            elif 'buy_vol' in item:
                b_vol = float(item.get('buy_vol', 0))
                s_vol = float(item.get('sell_vol', 0))
                if b_vol > 0: rows.append({'Broker': code, 'Action': 'BUY', 'Volume': b_vol, 'AvgPrice': float(item.get('buy_avg',0))})
                if s_vol > 0: rows.append({'Broker': code, 'Action': 'SELL', 'Volume': s_vol, 'AvgPrice': float(item.get('sell_avg',0))})
                
        if not rows: return None
        return pd.DataFrame(rows)

    def calculate_broker_net_history(self, historical_data, broker_code):
        """
        Calculates the Net Volume and Average Price of a specific broker over the entire history.
        """
        if not historical_data or not broker_code:
            return 0, 0
            
        total_buy_vol = 0
        total_buy_val = 0
        total_sell_vol = 0
        total_sell_val = 0
        
        for d_str, data in historical_data.items():
            for item in data:
                b_code = item.get('broker_code') or item.get('code')
                if b_code != broker_code:
                    continue
                    
                val = float(item.get('value', 0) or item.get('lot', 0))
                avg = float(item.get('avg', 0))
                side = item.get('side', '').upper()
                
                # Normalize legacy fields if needed, but assuming standard format first
                # Check legacy buy_vol/sell_vol if strict side not present
                if not side and 'buy_vol' in item:
                    # Legacy split
                    b_vol = float(item.get('buy_vol', 0))
                    s_vol = float(item.get('sell_vol', 0))
                    b_avg = float(item.get('buy_avg', 0))
                    s_avg = float(item.get('sell_avg', 0))
                    
                    total_buy_vol += b_vol
                    total_buy_val += (b_vol * b_avg)
                    total_sell_vol += s_vol
                    total_sell_val += (s_vol * s_avg)
                else:
                    # Standard side
                    if side == 'BUY':
                        total_buy_vol += val
                        total_buy_val += (val * avg)
                    elif side == 'SELL':
                        total_sell_vol += val
                        total_sell_val += (val * avg)
        
        net_vol = total_buy_vol - total_sell_vol
        
        # Calculate Avg Price of their net position
        # If Net Buy, use Buy Avg. If Net Sell, use Sell Avg? 
        # Or Total Value / Total Vol? 
        # Generally "Average Price Historis" means their avg cost.
        # Simple Weighted Average of all trades? Or just Buying avg?
        # Let's return the Weighted Average of the DOMINANT side.
        
        avg_price = 0
        if net_vol > 0 and total_buy_vol > 0:
            avg_price = total_buy_val / total_buy_vol
        elif net_vol < 0 and total_sell_vol > 0:
            avg_price = total_sell_val / total_sell_vol
            
        return net_vol, avg_price

    def calculate_dynamic_risk(self, entry_price, atr, method="aggressive"):
        """
        Manajemen Risiko Dinamis berbasis ATR.
        """
        if method == "conservative":
            multiplier = 2.0
            tp_multiplier = 3.0
        else: # aggressive/swing
            multiplier = 1.5
            tp_multiplier = 2.5
            
        sl_price = entry_price - (multiplier * atr)
        tp_price = entry_price + (tp_multiplier * atr)
        
        # Calculate Risk Percentage
        risk_pct = ((entry_price - sl_price) / entry_price) * 100
        
        return {
            "stop_loss": int(sl_price),
            "target_price": int(tp_price),
            "risk_percentage": round(risk_pct, 2),
            "risk_reward_ratio": f"1:{tp_multiplier/multiplier:.1f}"
        }

    def get_cumulative_broker_summary(self, historical_data):
        """
        Aggregates ALL broker data from history to find the Top Net Buyers and Sellers
        over the entire period.
        
        Returns:
            dict: {'top_buyers': [(code, vol)], 'top_sellers': [(code, vol)]}
        """
        if not historical_data:
            return {'top_buyers': [], 'top_sellers': []}
            
        broker_totals = {}
        
        for d_str, data in historical_data.items():
            for item in data:
                code = item.get('broker_code') or item.get('code')
                val = float(item.get('value', 0) or item.get('lot', 0))
                side = item.get('side', '').upper()
                
                if not code: continue
                
                # Normalize Volume (Positive for BUY, Negative for SELL)
                net_change = 0
                
                if side == 'BUY':
                    net_change = val
                elif side == 'SELL':
                    net_change = -val
                # Legacy check ignored for brevity as we generally see side
                elif 'buy_vol' in item:
                     b_vol = float(item.get('buy_vol', 0))
                     s_vol = float(item.get('sell_vol', 0))
                     net_change = b_vol - s_vol
                
                broker_totals[code] = broker_totals.get(code, 0) + net_change
                
        # Sort
        # Buyers: Net > 0, sorted const descending
        buyers = [(k, v) for k, v in broker_totals.items() if v > 0]
        buyers.sort(key=lambda x: x[1], reverse=True)
        
        # Sellers: Net < 0, sorted absolute descending (i.e. most negative first)
        sellers = [(k, v) for k, v in broker_totals.items() if v < 0]
        sellers.sort(key=lambda x: x[1]) # Ascending because they are negative (e.g. -1000 is smaller than -100)
        
        return {
            'top_buyers': buyers,
            'top_sellers': sellers
        }

    def calculate_final_verdict(self, tech_score, bandar_score, foreign_score, sentiment_score=50):
        """
        Menghitung Final Confidence Score (0-100%).
        
        Bobot:
        - Technical: 40%
        - Bandarmology: 30%
        - Foreign: 15%
        - Sentiment: 15%
        """
        # Normalisasi Skor
        # Tech Score asumsi 0-100 (input)
        # Bandar Score input -50 s/d +50 -> convert ke 0-100
        norm_bandar = bandar_score + 50 # Jadi 0-100
        
        # Foreign Score input -20 s/d +30 -> convert approx ke 0-100
        norm_foreign = 50 + (foreign_score * 1.5) 
        
        # Kalkulasi Weighted Average
        final_score = (
            (tech_score * 0.40) +
            (norm_bandar * 0.30) +
            (norm_foreign * 0.15) +
            (sentiment_score * 0.15)
        )
        
        final_score = min(100, max(0, final_score)) # Clamp
        
        verdict = "WAIT & SEE"
        if final_score >= 80:
            verdict = "STRONG BUY"
        elif final_score >= 60:
            verdict = "BUY / ACCUMULATE"
        elif final_score <= 30:
            verdict = "STRONG SELL"
        elif final_score <= 45:
            verdict = "SELL / AVOID"
            
        return {
            "final_score": int(final_score),
            "verdict": verdict,
            "details": {
                "technical_contribution": tech_score * 0.4,
                "bandar_contribution": norm_bandar * 0.3,
                "foreign_contribution": norm_foreign * 0.15
            }
        }

    def prepare_broker_flow_data(self, historical_data, top_n=3):
        """
        Prepares a DataFrame for Broker Flow Chart (Cumulative Net Volume).
        Targets the Top N Buyers and Sellers from the cumulative summary.
        """
        if not historical_data:
            return None
            
        # 1. Identify Key Brokers (Top N Buyers + Top N Sellers)
        summ = self.get_cumulative_broker_summary(historical_data)
        
        target_brokers = set()
        for b, _ in summ.get('top_buyers', [])[:top_n]:
            target_brokers.add(b)
        for b, _ in summ.get('top_sellers', [])[:top_n]:
            target_brokers.add(b)
            
        target_brokers = list(target_brokers)
        if not target_brokers:
            return None
            
        # 2. Build Time Series
        # Structure: {Date: {Broker: DailyNet}}
        sorted_dates = sorted(historical_data.keys())
        rows = []
        
        for d_str in sorted_dates:
            daily_raw = historical_data[d_str]
            row = {'Date': pd.to_datetime(d_str)}
            
            # Initialize 0 for all targets
            for b in target_brokers:
                row[b] = 0
                
            for item in daily_raw:
                code = item.get('broker_code') or item.get('code')
                if code not in target_brokers:
                    continue
                    
                val = float(item.get('value', 0) or item.get('lot', 0)) # Using Value if available (see prior logic)
                
                side = item.get('side', '').upper()
                
                net_change = 0
                if side == 'BUY':
                    net_change = val
                elif side == 'SELL':
                    net_change = -val
                elif 'buy_vol' in item:
                     b_vol = float(item.get('buy_value', 0) or item.get('buy_vol', 0))
                     s_vol = float(item.get('sell_value', 0) or item.get('sell_vol', 0))
                     net_change = b_vol - s_vol
                
                row[code] += net_change
            
            rows.append(row)
            
        if not rows:
            return None
            
        df = pd.DataFrame(rows)
        df.set_index('Date', inplace=True)
        
        # 3. Calculate Cumulative Sum (The "Flow")
        df_flow = df.cumsum()
        
        return df_flow
