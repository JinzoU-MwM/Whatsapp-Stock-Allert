import os
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_ai_analysis(ticker, ta_data, news_summary=""):
    """
    Uses Gemini to analyze the provided Technical Data AND News.
    """
    # Re-check API key here
    current_api_key = os.getenv("GOOGLE_API_KEY")
    if not current_api_key:
        return "Gemini API Key missing."
    
    genai.configure(api_key=current_api_key)

    print(f"Analyzing technical data for {ticker}...")
    
    try:
        # Get configured model from env, default to flash-exp
        model_name = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")
        print(f"[*] Using AI Model: {model_name}")
        
        model = genai.GenerativeModel(model_name) 
        
        # Construct Analysis Prompt
        prompt = f"""
        Bertindaklah sebagai Analis Saham Profesional Senior (Technical & Fundamental).
        Tugasmu adalah menganalisis data untuk saham {ticker}.
        
        1. DATA TEKNIKAL & VOLUME FLOW (DATAFAKTA):
        - FINAL VERDICT: {ta_data.get('verdict', 'N/A')} (Score: {ta_data.get('final_score', 0)}/100)
        - Harga Terakhir: {ta_data['price']:.0f}
        - Tren Utama: {ta_data['trend']} (Weekly: {ta_data.get('major_trend', 'N/A')})
        - Kekuatan Tren (ADX): {ta_data.get('adx', 0):.2f} (Jika >25=Trending, <20=Sideways)
        - Candle Pattern: {ta_data.get('candle_pattern', 'N/A')}
        - MACD (Momentum): {ta_data['macd_status']} (Hist: {ta_data['macd_hist']:.2f})
        - Bollinger Bands: {ta_data['bb_status']}
        - RSI (14): {ta_data['rsi']:.2f} | MFI (Money Flow): {ta_data.get('mfi', 50):.2f}
        - Volume Status: {ta_data['vol_status']} ({ta_data['vol_ratio']:.2f}x avg)
        - BANDARMOLOGY (Broker Summary): {ta_data['bandar_status']}
        - DETAIL BANDAR (Top Buyer/Seller): {ta_data.get('bandar_summary', '-')}
        - FOREIGN FLOW (Asing): {ta_data.get('foreign_status', 'N/A')}
        - Major Holder (Context): {ta_data.get('major_holders', 'N/A')}
        - Support: {ta_data['support']:.0f} | Resistance: {ta_data['resistance']:.0f}
        - Volatilitas (ATR): {ta_data.get('atr', 0):.0f} (Basis SL/TP)
        
        2. SENTIMEN BERITA (REAL-TIME):
        {news_summary}
        
        3. VALUASI FUNDAMENTAL (YFINANCE):
        - Status Valuasi: {ta_data.get('valuation', {}).get('valuation_status', 'N/A')}
        - PER (Price to Earnings): {ta_data.get('valuation', {}).get('per', 0):.2f}x
        - PBV (Price to Book): {ta_data.get('valuation', {}).get('pbv', 0):.2f}x
        - ROE (Return on Equity): {ta_data.get('valuation', {}).get('roe', 0) * 100:.2f}%
        - Market Cap: {ta_data.get('valuation', {}).get('market_cap', 0) / 1_000_000_000:.0f} Miliar IDR
        
        TUGAS UTAMA: 
        Analisis data di atas secara holistik (Teknikal + Fundamental + Bandarmology).
        Jika Fundamental bagus (ROE tinggi, PER wajar) dan Teknikal konfirmasi (Breakout/Reversal), berikan bobot lebih tinggi.
        
        PENTING - BANDARMOLOGY:
        - Prioritaskan data "BANDARMOLOGY (Broker Summary)" dan "DETAIL BANDAR" di atas untuk wawasan akumulasi/distribusi.
        - Gunakan sentimen berita sebagai pendukung, BUKAN sumber utama data bandar (kecuali data broker kosong).
        - Jika "DETAIL BANDAR" berisi kode broker (misal: AK, ZP, BK), sebutkan peran mereka (Institusi/Asing) dalam analisis.
        
        FORMAT OUTPUT (JSON):
        Keluarkan jawaban HANYA dalam format JSON valid ini (tanpa markdown ```json):
        {{
            "sentiment_score": (integer 0-100, dimana 0=Sangat Bearish, 50=Netral, 100=Sangat Bullish),
            "analysis": "Teks analisis lengkap kamu disini (Bahasa Indonesia, max 200 kata, gunakan emoji, layout poin-poin rapi)."
        }}
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Robust JSON cleaning
        import re
        # Find the first { and the last }
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                import json
                return json.loads(json_str)
            except:
                pass # Continue to fallback if regex match isn't valid JSON
        
        # Fallback manual cleaning
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
            
        import json
        try:
            return json.loads(text)
        except:
            # Fallback if JSON fails
            return {
                "sentiment_score": 50,
                "analysis": text
            }
        
    except Exception as e:
        return {
            "sentiment_score": 50,
            "analysis": f"Error analyzing data: {str(e)}"
        }
