import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

def _get_model():
    """Helper to configure and return the Gemini model."""
    current_api_key = os.getenv("GOOGLE_API_KEY")
    if not current_api_key:
        return None
    
    genai.configure(api_key=current_api_key)
    model_name = os.getenv("AI_MODEL", "gemini-1.5-flash")
    
    tools = [{"google_search": {}}]
    try:
        return genai.GenerativeModel(model_name, tools=tools)
    except:
        print("Warning: Google Search Grounding not supported. Using standard model.")
        return genai.GenerativeModel(model_name)

def _clean_json_response(text):
    """Helper to extract and parse JSON from AI response."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except:
        return {
            "sentiment_score": 50,
            "analysis": text,
            "status": "ERROR",
            "action": "WAIT"
        }

# --- 1. TECHNICAL AGENT (USER VERSION) ---
def get_technical_analysis(ticker, ta_data, news_summary=""):
    """
    Supercharged Technical Agent.
    Focus: Market Structure, Trend, Momentum, Volatility.
    """
    model = _get_model()
    if not model: return {"sentiment_score": 50, "analysis": "API Key Missing"}

    print(f"Catalyst: Running Technical Strategy for {ticker}...")
    
    prompt = f"""
    Bertindaklah sebagai Senior Trader & Risk Manager. 
    Tugasmu bukan hanya membaca indikator, tapi menyusun TRADING PLAN untuk saham {ticker}.
    
    [ANTI-HALLUCINATION POLICY]:
    1. STRICTLY use the provided data below. Do NOT invent numbers.
    2. If data is 'N/A' or 0, state it as "Unknown" or "Neutral".
    3. Do not assume news if not provided in "BERITA & SENTIMEN".
    4. LANGUAGE: STRICTLY INDONESIAN (BAHASA INDONESIA). Do not use English for the analysis text.

    DATA PASAR (DATAFAKTA):
    - Harga Terakhir: {ta_data['price']:.0f}
    - Tren (ADX {ta_data.get('adx', 0):.2f}): {ta_data['trend']} (Kondisi: {'>25=Strong Trend' if ta_data.get('adx',0)>25 else '<20=Choppy/Sideways'})
    - Volume: {ta_data['vol_status']} ({ta_data['vol_ratio']:.2f}x rata-rata). 
      (Note: Jika harga turun tapi volume meledak >2x, waspada panic selling/distribution).
    - Momentum (RSI): {ta_data['rsi']:.2f} | (MACD): {ta_data['macd_status']}
    - Volatilitas (ATR): {ta_data.get('atr', 0):.0f} (Gunakan ini untuk tentukan jarak Stop Loss).
    
    DATA HISTORIS SINGKAT:
    {ta_data.get('recent_history', 'N/A')}
    
    LEVEL PIVOT & FIBONACCI (SUPPORT/RESISTANCE REFERENSI):
    - Pivot: {ta_data.get('pivots', {}).get('pivot', 'N/A')}
    - Support (Classic): S1={ta_data.get('pivots', {}).get('s1', 'N/A')}, S2={ta_data.get('pivots', {}).get('s2', 'N/A')}
    - Resistance (Classic): R1={ta_data.get('pivots', {}).get('r1', 'N/A')}, R2={ta_data.get('pivots', {}).get('r2', 'N/A')}
    
    - Fibonacci Retracement:
      0.236: {ta_data.get('fib_levels', {}).get(0.236, 'N/A'):.0f}
      0.382: {ta_data.get('fib_levels', {}).get(0.382, 'N/A'):.0f} (Key Support)
      0.618: {ta_data.get('fib_levels', {}).get(0.618, 'N/A'):.0f} (Golden Pocket)
    
    (Gunakan level ini untuk menentukan Entry, SL, dan TP yang presisi)

    BERITA & SENTIMEN:
    {news_summary}

    TUGAS ANALISIS (Thinking Process):
    1. Cek Market Structure: Apakah Higher High (Uptrend) atau Lower Low (Downtrend)?
    2. Cek Divergence: Apakah ada anomali antara Harga vs Indikator?
    3. Tentukan Skenario:
       - Skenario Bullish (Jika breakout/rebound).
       - Skenario Bearish (Jika breakdown).

    OUTPUT YANG DIMINTA (JSON):
    {{
        "sentiment_score": (0-100, <40=Bearish, >60=Bullish),
        "analysis": "Analisis teknikal padat (max 150 kata). Fokus pada Price Action & Volume.",
        "action": "BUY_ON_WEAKNESS / BUY_ON_BREAKOUT / WAIT_AND_SEE / SELL / AVOID",
        "trading_plan": {{
            "buy_area": "Range harga beli (Wajib isi, jika Bearish isi area Support terdekat untuk pantau)",
            "stop_loss": "Harga SL (Critical Support - 1 ATR)",
            "target_profit": "Target harga (Resistance)"
        }},
        "plan_note": "Isi pesan tambahan jika plan ini high risk atau 'Wait for Confirmation'"
    }}
    """
    try:
        response = model.generate_content(prompt)
        return _clean_json_response(response.text.strip())
    except Exception as e:
        return {"sentiment_score": 50, "analysis": f"Error: {e}"}

# --- 2. BANDARMOLOGY AGENT (UPDATED USER VERSION) ---
def get_bandarmology_analysis(ticker, context_data):
    """
    Forensic Bandarmology Agent.
    Includes Foreign Flow, Valuation Context, and Detailed Broker Forensics.
    """
    model = _get_model()
    if not model: return {"sentiment_score": 50, "analysis": "API Key Missing"}

    print(f"Catalyst: Running Bandarmology Forensics for {ticker}...")
    
    # Extract Context
    bs_today = context_data.get('today_summary', 'N/A')
    seller_code = context_data.get('top_seller', 'N/A')
    seller_hist = context_data.get('seller_hist_net', 'N/A')
    avg_price_seller = context_data.get('seller_avg_price', 0)
    
    # Extract Additional Context
    vwap = context_data.get('vwap', 0)
    price_change = context_data.get('price_change', 0)
    top1_buy_price = context_data.get('top1_buy_price', 0)
    
    # Granular Broker Data
    top3_buyers_raw = context_data.get('top3_buyers', '-')
    top3_sellers_raw = context_data.get('top3_sellers', '-')
    
    # Valuation & Foreign
    pbv = context_data.get('pbv', 0)
    per = context_data.get('per', 0)
    market_cap = context_data.get('market_cap', 0)
    foreign_flow = context_data.get('foreign_flow', 'N/A')
    
    # Format Market Cap
    if market_cap > 1_000_000_000_000: mcap_str = f"{market_cap/1e12:.2f} Triliun"
    elif market_cap > 1_000_000_000: mcap_str = f"{market_cap/1e9:.0f} Miliar"
    else: mcap_str = f"{market_cap:,.0f}"
    
    prompt = f"""
    ROLE: Investigator Bandarmologi Profesional (Market Flow Detective).
    TUGAS: Analisis aliran dana institusi (smart money) menggunakan metode TOP-DOWN (Peta Besar vs Trigger Harian).

    [DATA INTEGRITY RULES]:
    1. Base your analysis PURELY on the Forensik Data below.
    2. Do NOT mention specific broker names (ZP, BK, etc.) unless they appear in [PETA KEKUATAN].
    3. LANGUAGE: STRICTLY INDONESIAN (BAHASA INDONESIA).
    
    --- DATA FORENSIK ---
    
    1. THE MAP (PETA BESAR - {context_data.get('periodic_period', 'N/A')} Hari Terakhir):
    - Fase: {context_data.get('periodic_status', 'N/A')}
    - Penguasa: {context_data.get('periodic_buyer_type', 'N/A')}
    - Top Accumulator: {context_data.get('periodic_top_accum', 'N/A')}
    - Avg Price Bandar: {context_data.get('periodic_avg_price', 0):,.0f} (vs Harga Market: {context_data.get('market_price', 0):,.0f})
    
    2. THE TRIGGER (HARI INI):
    - Status Hari Ini: {bs_today}
    - Top 3 Buyer: {top3_buyers_raw}
    - Top 3 Seller: {top3_sellers_raw}
    - Dominasi Volume: {context_data.get('daily_dominance', 'N/A')}
    
    [VALUASI & CONTEXT]:
    - Market Cap: {mcap_str}
    - PBV: {pbv:.2f}x
    - Foreign Flow: {foreign_flow}
    
    --- LOGIKA DETEKSI (TOP-DOWN ANALYSIS) ---
    Gunakan logika ini untuk kesimpulan:
    
    1. [STRONG BUY SIGNAL]: 
       - Peta Besar = AKUMULASI (Institusi).
       - Harga Market DEKAT dengan Avg Price Bandar.
       - Trigger Hari Ini = AKUMULASI (Institusi beli lagi).
       
    2. [JEBAKAN / TRAP]:
       - Peta Besar = DISTRIBUSI.
       - Trigger Hari Ini = Akumulasi (Hanya pancingan/mark-up sesaat).
       - Tindakan: Hati-hati / Sell on Strength.
       
    3. [MARKDOWN ACCUMULATION]:
       - Peta Besar = Akumulasi.
       - Trigger Hari Ini = Harga Turun tapi Institusi tampung (Net Buy).
       - Tindakan: Cicil Beli (Buy on Weakness).

    --- FORMAT OUTPUT JSON ---
    {{
        "sentiment_score": (0=Distribusi Total, 50=Netral, 100=Strong Accumulation),
        "status": "DISTRIBUSI / AKUMULASI / MARK-DOWN / CHURNING",
        "analysis": "Analisis naratif tajam (Max 150 kata). Fokus pada hubungan Peta Besar vs Trigger Hari Ini. Apakah hari ini valid atau jebakan?",
        "action": "BUY / WAIT / SELL"
    }}
    """
    try:
        response = model.generate_content(prompt)
        return _clean_json_response(response.text.strip())
    except Exception as e:
        return {"sentiment_score": 50, "analysis": f"Error: {e}"}

# --- 3. FUNDAMENTAL AGENT (ADDED) ---
def get_fundamental_analysis(ticker, financial_data):
    """
    Fundamental Agent.
    Focus: Valuation (Cheap/Expensive) & Health (Safe/Risky).
    """
    model = _get_model()
    if not model: return {"sentiment_score": 50, "analysis": "API Key Missing"}

    print(f"Catalyst: Running Fundamental Scan for {ticker}...")

    prompt = f"""
    Bertindaklah sebagai Senior Equity Research Analyst (Value Investing approach).
    Analisis kesehatan finansial emiten {ticker}.
    
    [STRICT DATA ONLY]:
    - Use the provided Financial Data ratios.
    - Do not retrieve outside data.
    - If a ratio is 'N/A', ignore it or label as 'Data Unavailable'.
    - LANGUAGE: STRICTLY INDONESIAN (BAHASA INDONESIA). Use formal investment terms in Indonesian.

    DATA KEUANGAN:
    - PE Ratio: {financial_data.get('pe_ratio', 'N/A')}
    - PBV: {financial_data.get('pbv', 'N/A')}
    - ROE: {financial_data.get('roe', 'N/A')}%
    - DER (Debt to Equity): {financial_data.get('der', 'N/A')}x
    - EPS Growth (YoY): {financial_data.get('eps_growth', 'N/A')}%

    TUGAS:
    1. Valuasi: Apakah saham ini Undervalued, Fair, atau Overvalued?
    2. Kesehatan: Apakah utang aman (DER < 1.5)? Profitabilitas kuat (ROE > 10%)?
    3. Growth: Apakah perusahaan bertumbuh?

    OUTPUT JSON:
    {{
        "sentiment_score": (0-100, <40=Bad Fundamentals, >70=Strong Fundamentals),
        "valuation_status": "UNDERVALUED / FAIR / OVERVALUED",
        "financial_health": "HEALTHY / RISKY / DISTRESS",
        "analysis": "Ringkasan fundamental max 100 kata. Highlight rasio kunci."
    }}
    """
    try:
        response = model.generate_content(prompt)
        return _clean_json_response(response.text.strip())
    except Exception as e:
        return {"sentiment_score": 50, "analysis": f"Error: {e}"}

# --- 4. SYNTHESIZER AGENT / CIO (ADDED) ---
def get_final_verdict(ticker, tech_res, bandar_res, fund_res):
    """
    The Boss Agent.
    Combines Technical + Bandarmology + Fundamental into one final decision.
    """
    model = _get_model()
    if not model: return {"final_score": 0, "final_reasoning": "Model Error"}
    
    print(f"Catalyst: Synthesizing Final Verdict for {ticker}...")

    prompt = f"""
    Anda adalah Chief Investment Officer (CIO). Anda menerima 3 laporan untuk saham {ticker}.
    Ambil keputusan final: BELI, JUAL, atau TAHAN.

    1. LAPORAN TEKNIKAL:
       - Score: {tech_res.get('sentiment_score')} | Action: {tech_res.get('action')}
       - Plan: {tech_res.get('trading_plan', {})}
       - Insight: {tech_res.get('analysis')}

    2. LAPORAN BANDARMOLOGI:
       - Score: {bandar_res.get('sentiment_score')} | Status: {bandar_res.get('status')}
       - Insight: {bandar_res.get('analysis')}

    3. LAPORAN FUNDAMENTAL (WAJIB DIPERTIMBANGKAN):
       - Score: {fund_res.get('sentiment_score')} 
       - STATUS VALUASI: {fund_res.get('valuation_status')} (Undervalued/Fair/Overvalued)
       - Insight: {fund_res.get('analysis')}

    LOGIKA PENIMBANGAN (WEIGHTING):
    - Jika Fundamental JELEK tapi Teknikal & Bandar BAGUS -> "Speculative Buy" (Short Term only).
    - Jika Fundamental BAGUS dan Teknikal BAGUS -> "Strong Buy" (Swing/Invest).
    - Jika Bandarmologi "DISTRIBUSI MASIF", abaikan sinyal Buy teknikal (Risk of False Breakout).
    - Jika Teknikal "Downtrend" tapi Fundamental & Bandar Bagus -> "Wait for Reversal" (Watchlist).

    [REQUIREMENT: DETAILED ACTION PLAN]:
    Provide a specific execution strategy including:
    1. "Risk 1% Rule" calculation example (Assume 100 Mio Portfolio -> Max Risk 1 Mio).
    2. Position Sizing advice (e.g. "Potong Size 1/3", "Cicil Beli").
    3. Strict Exit rules (e.g. "Buang jika closing di bawah support").
    
    LANGUAGE: STRICTLY INDONESIAN (BAHASA INDONESIA). Semua output harus dalam Bahasa Indonesia.

    OUTPUT JSON:
    {{
        "final_score": (0-100),
        "primary_strategy": "SWING_TRADE / INVESTING / SCALPING / AVOID",
        "conviction_level": "HIGH / MEDIUM / LOW",
        "final_reasoning": "Kesimpulan tegas max 3 kalimat. Gabungkan ketiga perspektif.",
        "recommended_action": "BUY / SELL / WAIT",
        "allocation_size": "SMALL (5%) / MEDIUM (15%) / AGGRESSIVE (25%) / ZERO",
        "action_plan": "Tulis rencana eksekusi detail (Risk Rule, Cicil Beli, Cut Loss) dalam format poin-poin singkat."
    }}
    """
    try:
        response = model.generate_content(prompt)
        return _clean_json_response(response.text.strip())
    except Exception as e:
        return {"final_score": 0, "final_reasoning": f"Error: {e}"}

# --- MAIN RUNNER EXAMPLE ---
if __name__ == "__main__":
    # Contoh Data Dummy (Anda ganti dengan data real dari API/Database Anda)
    ticker = "BBRI"
    
    # 1. Dummy Technical Data
    ta_data = {
        "price": 4500, "trend": "Uptrend", "adx": 30, "vol_status": "High", 
        "vol_ratio": 1.5, "rsi": 65, "macd_status": "Golden Cross", "atr": 50,
        "recent_history": "Saham rebound dari support 4300."
    }
    
    # 2. Dummy Bandarmology Data
    bandar_data = {
        "today_summary": "ZP dan AK akumulasi masif.",
        "top_seller": "YP", "seller_hist_net": "Netral", "seller_avg_price": 4480,
        "vwap": 4490, "price_change": 2.5, "top1_buy_price": 4510,
        "top3_buyers": "ZP, AK, BK", "top3_sellers": "YP, PD, CC",
        "market_cap": 600_000_000_000_000, "pbv": 2.5, "per": 12, "foreign_flow": "Net Buy 50B"
    }

    # 3. Dummy Fundamental Data
    fund_data = {
        "pe_ratio": 12.5, "pbv": 2.5, "roe": 18, "der": 0.8, "eps_growth": 10
    }

    # Execute Pipeline
    tech_res = get_technical_analysis(ticker, ta_data)
    bandar_res = get_bandarmology_analysis(ticker, bandar_data)
    fund_res = get_fundamental_analysis(ticker, fund_data)
    
    final = get_final_verdict(ticker, tech_res, bandar_res, fund_res)
    
    print("\n--- FINAL VERDICT ---")
    print(json.dumps(final, indent=2))