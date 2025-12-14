import requests
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

import requests
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

class GoApiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOAPI_API_KEY")
        # Fixed URL: .io instead of .id
        self.base_url = "https://api.goapi.io/stock/idx"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json"
        }

    def check_connection(self):
        """Simple check to verify API Key validity."""
        if not self.api_key:
            return False
        try:
            # Test with a lightweight endpoint
            # We use broker_summary with a known date to ensure connectivity
            # or just a company profile endpoint if available.
            # Let's try to fetch BBCA broker summary for a specific date (fallback test)
            url = f"{self.base_url}/BBCA/broker_summary?date=2024-01-01"
            response = requests.get(url, headers=self.headers, timeout=5)
            # 200 or 400 or even 404 (if ticker valid but data empty) means connection is OK.
            # Connection error would raise Exception.
            return True
        except:
            return False

    def _get_last_trading_day(self):
        """Helper to get the last likely trading day (e.g., skip weekends)."""
        today = datetime.date.today()
        weekday = today.weekday() # 0=Mon, 6=Sun
        
        # If Sat (5) or Sun (6), go back to Friday
        if weekday == 5: # Saturday
            last_trading = today - datetime.timedelta(days=1)
        elif weekday == 6: # Sunday
            last_trading = today - datetime.timedelta(days=2)
        else:
            # Weekday
            # If it's early morning, maybe data for today isn't ready?
            # For simplicity, we try Today. If it returns empty, logic elsewhere could retry Yesterday.
            # But let's default to Today for now.
            last_trading = today
            
        return last_trading.strftime("%Y-%m-%d")

    def get_broker_summary(self, ticker, date=None):
        """
        Fetches Broker Summary for a specific ticker.
        If date is None, attempts to auto-detect last trading day.
        """
        if not self.api_key: return None
        
        if not date:
            date = self._get_last_trading_day()
            
        url = f"{self.base_url}/{ticker}/broker_summary"
        params = {"date": date}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'results' in data['data']:
                    # Return the list of brokers directly
                    return data['data']['results']
            return None
        except Exception as e:
            print(f"GoAPI Broker Summary Error: {e}")
            return None

    def get_foreign_flow(self, ticker, date=None):
        """
        Fetches Foreign Flow by using Broker Summary with investor=FOREIGN.
        Calculates Net Foreign Buy/Sell from the top brokers returned.
        """
        if not self.api_key: return None
        
        if not date:
            date = self._get_last_trading_day()
        
        url = f"{self.base_url}/{ticker}/broker_summary"
        params = {"date": date, "investor": "FOREIGN"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'results' in data['data']:
                    # Process the foreign broker list to calculate Net Foreign
                    results = data['data']['results']
                    
                    # Calculate Net Buy/Sell
                    net_foreign = 0.0
                    total_buy = 0.0
                    total_sell = 0.0
                    
                    # Each item has 'side' (BUY/SELL) and 'value'
                    # API response format in debug was:
                    # {"code":"AK", "side":"BUY", "value":139..., "transaction_type":"NET"}
                    # It seems to list brokers and their NET position for the day? 
                    # "transaction_type":"NET" implies this line is the net for that broker.
                    
                    for item in results:
                        val = float(item.get('value', 0))
                        side = item.get('side', '').upper()
                        
                        # Assuming the list contains Net Buy and Net Sell entries for brokers
                        if side == 'BUY':
                            total_buy += val
                            net_foreign += val
                        elif side == 'SELL':
                            total_sell += val
                            net_foreign -= val
                            
                    return [{
                        'date': date,
                        'net_foreign_buy': net_foreign, # This will be negative if sell > buy
                        'total_buy': total_buy,
                        'total_sell': total_sell
                    }]
            return None
        except Exception as e:
            print(f"GoAPI Foreign Flow Error: {e}")
            return None
