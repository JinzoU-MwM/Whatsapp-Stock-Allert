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
            # We use historical endpoint which is standard
            url = f"{self.base_url}/BBCA/historical"
            response = requests.get(url, headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    def _get_trading_dates(self):
        """
        Returns a list of dates to try: [Today, Yesterday/LastBusinessDay].
        """
        today = datetime.date.today()
        dates = [today]
        
        # Calculate last trading day (EOD fallback)
        last_trading = today - datetime.timedelta(days=1)
        if last_trading.weekday() == 5: # Sat -> Fri
            last_trading -= datetime.timedelta(days=1)
        elif last_trading.weekday() == 6: # Sun -> Fri
            last_trading -= datetime.timedelta(days=2)
            
        dates.append(last_trading)
        return dates

    def get_broker_summary(self, ticker, date=None):
        """
        Fetches Broker Summary.
        If date is None, tries TODAY first, then falls back to LAST TRADING DAY.
        """
        if not self.api_key: return None
        
        target_dates = [date] if date else self._get_trading_dates()
        
        for d in target_dates:
            d_str = d.strftime("%Y-%m-%d") if isinstance(d, datetime.date) else d
            # print(f"DEBUG: Trying Broker Summary for {d_str}")
            
            url = f"{self.base_url}/{ticker}/broker_summary"
            params = {"date": d_str}
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'results' in data['data']:
                        results = data['data']['results']
                        if results: # If not empty
                            return results
            except Exception as e:
                print(f"GoAPI Broker Summary Error ({d_str}): {e}")
                
        return None

    def get_foreign_flow(self, ticker, date=None):
        """
        Fetches Foreign Flow (Net Foreign Buy/Sell).
        Tries TODAY first, then falls back to LAST TRADING DAY.
        """
        if not self.api_key: return None
        
        target_dates = [date] if date else self._get_trading_dates()
        
        for d in target_dates:
            d_str = d.strftime("%Y-%m-%d") if isinstance(d, datetime.date) else d
            
            url = f"{self.base_url}/{ticker}/broker_summary"
            params = {"date": d_str, "investor": "FOREIGN"}
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'results' in data['data']:
                        results = data['data']['results']
                        if results:
                            # Calculate Net Foreign
                            net_foreign = 0.0
                            total_buy = 0.0
                            total_sell = 0.0
                            
                            for item in results:
                                val = float(item.get('value', 0))
                                side = item.get('side', '').upper()
                                
                                if side == 'BUY':
                                    total_buy += val
                                    net_foreign += val
                                elif side == 'SELL':
                                    total_sell += val
                                    net_foreign -= val
                                    
                            return [{
                                'date': d_str,
                                'net_foreign_buy': net_foreign,
                                'total_buy': total_buy,
                                'total_sell': total_sell
                            }]
            except Exception as e:
                print(f"GoAPI Foreign Flow Error ({d_str}): {e}")
                
        return None

    def get_latest_price(self, ticker):
        """
        Fetches the latest snapshot price for a ticker.
        """
        if not self.api_key: return None
        
        url = f"{self.base_url}/prices"
        params = {"symbols": ticker}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Handle nested data structure
                if 'data' in data:
                    d = data['data']
                    results = None
                    
                    if isinstance(d, dict) and 'results' in d:
                        results = d['results']
                    elif isinstance(d, list):
                        results = d
                        
                    if results and len(results) > 0:
                        return results[0] # Return the first/only result
        except Exception as e:
            print(f"GoAPI Latest Price Error: {e}")
            
        return None

    def get_historical_data(self, ticker, from_date=None, to_date=None):
        """
        Fetches historical price data (Open, High, Low, Close, Volume).
        Returns list of dicts.
        """
        if not self.api_key: return None
        
        url = f"{self.base_url}/{ticker}/historical"
        params = {}
        if from_date: params['from'] = from_date
        if to_date: params['to'] = to_date
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    # Support both formats:
                    # 1. {'data': {'results': [...]}} (Current .io behavior)
                    # 2. {'data': [...]} (Alternative/User suggested behavior)
                    d = data['data']
                    if isinstance(d, dict) and 'results' in d:
                        return d['results']
                    elif isinstance(d, list):
                        return d
        except Exception as e:
            print(f"GoAPI Historical Error: {e}")
        
        return None
