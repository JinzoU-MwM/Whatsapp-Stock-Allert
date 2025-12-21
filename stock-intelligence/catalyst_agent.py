import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def _get_model():
    """Helper to configure and return the Gemini model."""
    current_api_key = os.getenv("GOOGLE_API_KEY")
    if not current_api_key:
        return None
    
    genai.configure(api_key=current_api_key)
    # Get configured model from env, default to gemini-1.5-flash (Fastest/Stable)
    model_name = os.getenv("AI_MODEL", "gemini-1.5-flash")
    
    # Enable Google Search Grounding ("MCP Browser" equivalent for Gemini)
    # This allows the model to search the web for catalysts if it needs more info.
    tools = [
        {"google_search": {}} 
    ]
    
    # Try initializing with tools (supported in recent SDKs)
    try:
        return genai.GenerativeModel(model_name, tools=tools)
    except:
        # Fallback for older SDKs
        print("Warning: Google Search Grounding not supported in this SDK version. Using standard model.")
        return genai.GenerativeModel(model_name)

def _clean_json_response(text):
    """Helper to extract and parse JSON from AI response."""
    import re
    import json
    
    # 1. Regex Match for JSON block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass

    # 2. Markdown Cleanup
    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()

    # 3. Direct Parse
    try:
        return json.loads(text)
    except:
        # Fallback
        return {
            "sentiment_score": 50,
            "analysis": text
        }

# --- 1. TECHNICAL AGENT ---
def get_technical_analysis(ticker, ta_data, news_summary=""):
    """
    Supercharged Technical Agent.
    Now includes: Psychology reading, Divergence check, and ATR-based Targets.
    """
    model = _get_model()
    if not model: return {"sentiment_score": 50, "analysis": "API Key Missing"}

    print(f"Catalyst: Running Technical Strategy for {ticker}...")
    
    prompt = f"""
    Bertindaklah sebagai Senior Trader & Risk Manager. 
    Tugasmu bukan hanya membaca indikator, tapi menyusun TRADING PLAN untuk saham {ticker}.

    DATA PASAR (DATAFAKTA):
    - Harga Terakhir: {ta_data['price']:.0f}
    - Tren (ADX {ta_data.get('adx', 0):.2f}): {ta_data['trend']} (Kondisi: {'>25=Strong Trend' if ta_data.get('adx',0)>25 else '<20=Choppy/Sideways'})
    - Volume: {ta_data['vol_status']} ({ta_data['vol_ratio']:.2f}x rata-rata). 
      (Note: Jika harga turun tapi volume meledak >2x, waspada panic selling/distribution).
    - Momentum (RSI): {ta_data['rsi']:.2f} | (MACD): {ta_data['macd_status']}
    - Volatilitas (ATR): {ta_data.get('atr', 0):.0f} (Gunakan ini untuk tentukan jarak Stop Loss).
    
    DATA HISTORIS SINGKAT:
    {ta_data.get('recent_history', 'N/A')}

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
            "buy_area": "Range harga beli ideal",
            "stop_loss": "Harga SL (Gunakan Low terdekat dikurang 1x ATR)",
            "target_profit": "Target harga realistis (Resistance terdekat)"
        }}
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        return _clean_json_response(response.text.strip())
    except Exception as e:
        return {"sentiment_score": 50, "analysis": f"Error: {e}"}

# --- 2. BANDARMOLOGY AGENT ---
def get_bandarmology_analysis(ticker, context_data):
    """
    Forensic Bandarmology Agent.
    Now capable of detecting 'Old Inventory Distribution' like the COAL case.
    """
    model = _get_model()
    if not model: return {"sentiment_score": 50, "analysis": "API Key Missing"}

    print(f"Catalyst: Running Bandarmology Forensics for {ticker}...")
    
    # Extract Context
    bs_today = context_data.get('today_summary', 'N/A')
    seller_code = context_data.get('top_seller', 'N/A')
    seller_hist = context_data.get('seller_hist_net', 'N/A') # Misal: "Net Buy 500 Juta" atau "Net Sell 0"
    avg_price_seller = context_data.get('seller_avg_price', 0)
    
    # Extract Additional Context
    vwap = context_data.get('vwap', 0)
    price_change = context_data.get('price_change', 0)
    top1_buy_price = context_data.get('top1_buy_price', 0)
    
    prompt = f"""
    ROLE: Investigator Bandarmologi Profesional (Market Flow Detective).
    TUGAS: Deteksi Kecurangan, Manipulasi, atau Pergerakan Smart Money di saham {ticker}.

    --- 1. DATA FORENSIK UTAMA ---
    [SUMMARY HARI INI]: 
    {bs_today}

    [JEJAK PENJUAL UTAMA (TOP SELLER)]:
    - Kode Broker: {seller_code}
    - Historis (Sebelum Hari Ini): {seller_hist}
    - Avg Price Jual Hari Ini: {avg_price_seller}

    [DATA TAMBAHAN]:
    - VWAP Hari Ini: {vwap:,.0f}
    - Perubahan Harga: {price_change:.2f}%
    - Avg Price Top 1 Buyer: {top1_buy_price:,.0f}

    --- 2. LOGIKA DETEKSI (WAJIB ANALISIS) ---

    A. [DISTRIBUSI BARANG LAMA - OLD INVENTORY]
       RULE: Jika Top Seller jualan MASIF hari ini, TAPI data historis kemaren-kemaren TIDAK ada akumulasi (Net Buy kecil/Nol).
       KESIMPULAN: "MEMBUANG BARANG LAMA" (Barang IPO/Founder/Treasury). 
       VERDICT: SANGAT BEARISH (Exit Strategy).

    B. [TRANSFER OF WEALTH - RITEL vs BANDAR]
       RULE: Cek Top Buyer vs Top Seller.
       - Seller Institusi -> Buyer Ritel (YP, PD, XL, XC, KK, CC, CP, EP)? => DISTRIBUSI.
       - Seller Institusi -> Buyer Institusi? => TUKAR BARANG / CROSSING.
       - Seller Ritel -> Buyer Institusi? => AKUMULASI.

    C. [PING-PONG / CHURNING - ARTIFICIAL VOLUME]
       RULE: 
         1. Volume Top Buyer ≈ Volume Top Seller (Selisih < 10%).
         2. Harga Stagnan (Change < 2%).
       KESIMPULAN: "ARTIFICIAL VOLUME". Volume palsu untuk memancing ritel.

    D. [MARKDOWN ACCUMULATION - AKUMULASI SENYAP]
       RULE:
         1. Harga TURUN (Merah).
         2. Top Buyer = Institusi/Asing.
         3. Avg Price Buyer <= Closing Price (Dapat barang bawah).
       KESIMPULAN: "ABSORPTION / BUY ON WEAKNESS". Sinyal Bullish tersembunyi.

    E. [POWER BUYER - AGGRESSIVE ACCUMULATION]
       RULE: Avg Price Top 1 Buyer > VWAP.
       KESIMPULAN: "AGGRESSIVE ACCUMULATION (HK)". Bandar berani beli mahal, indikasi target harga tinggi.

    --- 3. DAFTAR BROKER (UPDATE) ---
    - RITEL (LEMAH): YP, PD, XL, XC, KK, CC, CP (Valbury), EP (MNC).
    - HYBRID (SCALPER): MG (Semesta) - Sering hit & run, bukan akumulasi jangka panjang.

    --- 4. OUTPUT JSON ---
    {{
        "sentiment_score": (0=Distribusi Total, 50=Netral, 100=Akumulasi Kuat),
        "status": "DISTRIBUSI / AKUMULASI / MARK-DOWN / CHURNING",
        "analysis": "Analisis tajam max 150 kata. Gunakan Logic A-E di atas. Sebutkan siapa makan siapa.",
        "warning": "Berikan warning jika terdeteksi 'Jualan Barang Lama' atau 'Churning'."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        return _clean_json_response(response.text.strip())
    except Exception as e:
        return {"sentiment_score": 50, "analysis": f"Error: {e}"}

# Legacy wrapper for compatibility if needed
def get_ai_analysis(ticker, ta_data, news_summary=""):
    return get_technical_analysis(ticker, ta_data, news_summary)
