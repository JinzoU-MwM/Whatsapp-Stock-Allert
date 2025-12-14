import requests
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

class GoApiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOAPI_API_KEY")
        self.base_url = "https://api.goapi.id/v1/stock/idx"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json"
        }

    def check_connection(self):
        """Simple check to verify API Key validity."""
        if not self.api_key:
            return False
        try:
            # Test with a lightweight endpoint, e.g., fetching a popular ticker
            url = f"{self.base_url}/BBCA"
            response = requests.get(url, headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_broker_summary(self, ticker, date=None):
        """
        Fetches Broker Summary for a specific ticker and date.
        If date is None, uses today's date (or yesterday if market closed).
        Endpoint assumption: /companies/{ticker}/broker_summary or similar.
        """
        if not self.api_key: return None
        
        # Format date YYYY-MM-DD
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")
            
        # Endpoint path may vary, attempting standard pattern
        # Pattern 1: /stock/idx/{ticker}/broker_summary?date={date}
        url = f"{self.base_url}/{ticker}/broker_summary"
        params = {"date": date}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Validate data structure
                if 'data' in data:
                    return data['data']
            return None
        except Exception as e:
            print(f"GoAPI Broker Summary Error: {e}")
            return None

    def get_foreign_flow(self, ticker):
        """
        Fetches Foreign Flow (Net Buy/Sell) data.
        """
        if not self.api_key: return None
        
        url = f"{self.base_url}/{ticker}/foreign_flow"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
            return None
        except Exception as e:
            print(f"GoAPI Foreign Flow Error: {e}")
            return None
