
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOAPI_API_KEY")
# User suggested endpoint: /stock/idx/news
# Full URL likely: https://api.goapi.io/stock/idx/news

url = "https://api.goapi.io/stock/idx/news"
headers = {"X-API-KEY": api_key, "Accept": "application/json"}

print(f"Probing: {url}")

# Attempt 1: General News (Latest)
try:
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:500]}") # Print first 500 chars to see content
except Exception as e:
    print(f"Error: {e}")

# Attempt 2: With Symbol Parameter
print("\nProbing with symbol='BBCA'...")
try:
    resp = requests.get(url, headers=headers, params={'symbol': 'BBCA'}, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
