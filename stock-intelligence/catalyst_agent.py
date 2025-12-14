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
        # Using Gemini 2.0 Flash Exp (Smart & Fast) for reasoning
        model = genai.GenerativeModel('gemini-2.0-flash-exp') 
        
        # Construct Analysis Prompt
        prompt = f"""
        Bertindaklah sebagai Analis Saham Profesional Senior (Technical & Fundamental).
        Tugasmu adalah menganalisis data untuk saham {ticker}.
        
        1. DATA TEKNIKAL & VOLUME FLOW (DATAFAKTA):
        - Harga Terakhir: {ta_data['price']:.0f}
        - Tren Utama: {ta_data['trend']} (Weekly: {ta_data.get('major_trend', 'N/A')})
        - Kekuatan Tren (ADX): {ta_data.get('adx', 0):.2f} (Jika >25=Trending, <20=Sideways)
        - Candle Pattern: {ta_data.get('candle_pattern', 'N/A')}
        - MACD (Momentum): {ta_data['macd_status']} (Hist: {ta_data['macd_hist']:.2f})
        - Bollinger Bands: {ta_data['bb_status']}
        - RSI (14): {ta_data['rsi']:.2f} | MFI (Money Flow): {ta_data.get('mfi', 50):.2f}
        - Volume Status: {ta_data['vol_status']} ({ta_data['vol_ratio']:.2f}x avg)
        - SMART MONEY / BANDARMOLOGY: {ta_data['bandar_status']} ({ta_data['bandar_action']})
        - Major Holder (Context): {ta_data.get('major_holders', 'N/A')}
        - Support: {ta_data['support']:.0f} | Resistance: {ta_data['resistance']:.0f}
        - Volatilitas (ATR): {ta_data.get('atr', 0):.0f} (Basis SL/TP)
        
        2. SENTIMEN BERITA (REAL-TIME):
        {news_summary}
        
        TUGAS UTAMA: 
        Cari kata kunci "Net Buy", "Net Sell", "Asing", "Foreign", "Borong", atau "Guyur" di dalam berita.
        Jika ditemukan, jadikan itu sebagai "REAL BANDARMOLOGI insight".
        
        FORMAT OUTPUT (JSON):
        Keluarkan jawaban HANYA dalam format JSON valid ini (tanpa markdown ```json):
        {{
            "sentiment_score": (integer 0-100, dimana 0=Sangat Bearish, 50=Netral, 100=Sangat Bullish),
            "analysis": "Teks analisis lengkap kamu disini (Bahasa Indonesia, max 200 kata, gunakan emoji, layout poin-poin rapi)."
        }}
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean markdown if present
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "")
            
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
