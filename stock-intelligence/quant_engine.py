import pandas as pd
import numpy as np

class QuantAnalyzer:
    def __init__(self):
        # Daftar Broker Retail (Contoh)
        self.retail_brokers = ['YP', 'PD', 'CC', 'NI', 'XC', 'XL', 'KK']
        # Daftar Broker Institusi/Asing (Contoh)
        self.insti_brokers = ['BK', 'ZP', 'AK', 'KZ', 'RX', 'CS', 'CG']

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
        
        return {
            "status": status,
            "bandar_score": score,
            "top_buyer": top1_buyer,
            "buyer_type": buyer_type,
            "net_vol_ratio": net_vol_ratio,
            "avg_price_diff": avg_price_diff,
            "summary": f"{status}. Buyer Utama: {top1_buyer} ({buyer_type})."
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
            verdict = "STRONG BUY 🚀"
        elif final_score >= 60:
            verdict = "BUY / ACCUMULATE ✅"
        elif final_score <= 30:
            verdict = "STRONG SELL ❌"
        elif final_score <= 45:
            verdict = "SELL / AVOID ⚠️"
            
        return {
            "final_score": int(final_score),
            "verdict": verdict,
            "details": {
                "technical_contribution": tech_score * 0.4,
                "bandar_contribution": norm_bandar * 0.3,
                "foreign_contribution": norm_foreign * 0.15
            }
        }
