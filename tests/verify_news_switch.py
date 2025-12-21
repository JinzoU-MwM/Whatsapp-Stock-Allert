
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence')))

import news_fetcher

ticker = "BBCA.JK"
print(f"Fetching news for {ticker}...")
news = news_fetcher.fetch_stock_news(ticker)
print("\n[NEWS RESULT]")
print(news)

# Check if it came from GoAPI (by structure or log message if visible, but here we just check output content)
# GoAPI news output format I defined: "- [Title](url) date"
# Serper output format was: "- [Title](link): snippet"
if "Snippet" in news: 
    print("\n[SOURCE] Likely Serper (Snippet detected)")
else:
    print("\n[SOURCE] Likely GoAPI (No snippet, date present?)")
