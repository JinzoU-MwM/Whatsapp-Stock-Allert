import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def fetch_stock_news(ticker):
    """
    Fetches the latest news for a given ticker using Serper.dev API.
    Returns a summarized string of the top 3-5 news items.
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key or "your_serper" in api_key:
        return "⚠️ Pencarian Berita Dilewati: SERPER_API_KEY belum dikonfigurasi di .env."

    print(f"🌍 Mengambil Berita Real-Time untuk {ticker} via Serper...")
    
    url = "https://google.serper.dev/search"
    
    clean_ticker = ticker.replace(".JK", "")
    
    # Specific query for Indonesian market context
    if ".JK" in ticker:
        # Use quotes for exact match to avoid random news
        query = f'Saham "{clean_ticker}" berita terkini'
    else:
        query = f'"{clean_ticker}" stock news'

    payload = json.dumps({
        "q": query,
        "tbs": "qdr:w", # Past week
        "num": 10,      # Fetch more candidates for filtering
        "gl": "id",     # Geo location: Indonesia
        "hl": "id"      # Host language: Indonesia
    })
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        
        news_items = []
        if 'organic' in data:
            for item in data['organic']:
                title = item.get('title', 'No Title')
                snippet = item.get('snippet', 'No Snippet')
                link = item.get('link', '#')
                
                # STRICT FILTERING: Ticker must appear in Title or Snippet
                # This prevents unrelated news (like "IHSG up" showing for a specific stock)
                if clean_ticker.lower() in title.lower() or clean_ticker.lower() in snippet.lower():
                    news_items.append(f"- [{title}]({link}): {snippet}")
                
                # Limit to top 5 RELEVANT items
                if len(news_items) >= 5:
                    break
        
        if not news_items:
            return f"Tidak ada berita spesifik untuk {clean_ticker} dalam seminggu terakhir."
            
        return "\n".join(news_items)

    except Exception as e:
        return f"Gagal mengambil berita: {str(e)}"
