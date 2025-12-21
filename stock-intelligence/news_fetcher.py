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
    goapi_key = os.getenv("GOAPI_API_KEY")
    
    # 1. Try GoAPI First (User Requested)
    if goapi_key:
        try:
            from goapi_client import GoApiClient
            client = GoApiClient(goapi_key)
            news_list = client.get_news(ticker, limit=5)
            
            if news_list:
                print(f"Mengambil Berita Real-Time untuk {ticker} via GoAPI...")
                formatted_news = []
                for item in news_list:
                    # Adjust fields based on GoAPI response structure
                    title = item.get('title', 'No Title')
                    # some apis return 'published_at' or 'date'
                    date_str = item.get('published_at', '') or item.get('date', '')
                    url = item.get('url', '#')
                    # GoAPI might not have snippet, just title
                    formatted_news.append(f"- [{title}]({url}) {date_str}")
                
                return "\n".join(formatted_news)
        except Exception as e:
            print(f"GoAPI News Failed, falling back to Serper: {e}")

    # 2. Fallback to Serper
    if not api_key or "your_serper" in api_key:
        return "⚠️ Pencarian Berita Dilewati: SERPER_API_KEY belum dikonfigurasi di .env."

    try:
        print(f"Mengambil Berita Real-Time untuk {ticker} via Serper...")
    except:
        pass # Silently fail if print fails due to encoding
    
    url = "https://google.serper.dev/search"
    
    clean_ticker = ticker.replace(".JK", "")
    
    # Specific query for Indonesian market context
    # Specific query for Indonesian market context
    # Enforce Indonesia/IDX context strongly as requested by user
    if ".JK" in ticker or (len(clean_ticker) == 4 and clean_ticker.isalpha()):
        # Use quotes for exact match to avoid random news
        # Add "IDX" and "Indonesia" to ensure no other country's stock is fetched
        query = f'Saham "{clean_ticker}" IDX Indonesia berita terkini'
    else:
        # Fallback for others, but still bias towards ID via gl parameter below
        query = f'"{clean_ticker}" stock news Indonesia'

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

    # Retry Mechanism
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # User requested NOT to skip news, so we increase timeout to 15s
            response = requests.request("POST", url, headers=headers, data=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                break
            else:
                print(f"Serper Error (Attempt {attempt+1}): {response.status_code}")
        except Exception as e:
            print(f"Serper Timeout/Error (Attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                return f"Gagal mengambil berita setelah {max_retries} kali percobaan: {str(e)}"
    
    # Process Data if we have it (data variable might be unbound if all fail, handled by return above)
    try:
        if 'data' not in locals(): return "Gagal mengambil data berita."
        
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
