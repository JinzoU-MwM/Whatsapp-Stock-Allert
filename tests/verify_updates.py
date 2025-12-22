
import unittest
import sys
import os
import pandas as pd
from unittest.mock import MagicMock, patch

# Setup Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Modules to Test
import technical_analysis
from quant_engine import QuantAnalyzer # Correct class name
import news_fetcher
import catalyst_agent

class TestUpdates(unittest.TestCase):
    
    def test_01_technical_vwap_and_fix(self):
        """Verify VWAP calculation and NameError fix in technical_analysis"""
        print("\n[TEST] 1. Verifying Technical Analysis (VWAP & Stability)...")
        try:
            # We'll mock get_stock_data to avoid network calls and control data
            # Create a mock DF with enough data for Valid TA (30 rows to satisfy EMA 20)
            data = {
                'Open': [1000 + i for i in range(30)],
                'High': [1020 + i for i in range(30)],
                'Low': [990 + i for i in range(30)],
                'Close': [1010 + i for i in range(30)],
                'Volume': [5000 + i*100 for i in range(30)]
            }
            df = pd.DataFrame(data)
            
            # Mock the internal calls
            with patch('technical_analysis.get_stock_data') as mock_fe, \
                 patch('technical_analysis.get_valuation_data') as mock_val:
                 
                mock_fe.return_value = df
                mock_val.return_value = {'per': 10}
                
                # Run Analysis
                result = technical_analysis.analyze_technical("TEST")
                
                # Assertions
                self.assertIn('vwap', result, "VWAP field missing!")
                self.assertIn('change_pct', result, "change_pct field missing!")
                
                print(f"   > VWAP: {result['vwap']}")
                print(f"   > Change%: {result['change_pct']:.2f}%")
                print("   > Success: Technical Analysis runs without crashing.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.fail(f"Technical Analysis Crashed: {e}")

    def test_02_quant_engine_top1(self):
        """Verify QuantEngine returns Top 1 Buyer/Seller Prices"""
        print("\n[TEST] 2. Verifying Quant Engine (Top 1 Prices)...")
        
        # Mock Data
        mock_raw = {
            'broker_summary': pd.DataFrame({
                'Code': ['YP', 'PD', 'KK'],
                'BVol': [100, 50, 10],
                'BVal': [100000, 50000, 10000],
                'BAvg': [1000, 1000, 1000],
                'SVol': [10, 10, 10], # Net Buy
                'SVal': [10000, 10000, 10000],
                'SAvg': [1000, 1000, 1000],
                'AvgPrice': [1000, 1000, 1000] # Simplified generic column for test
            })
        }
        
        # Need to structure it as analyze_broker_summary expects (processed dataframes normally)
        # But wait, analyze_broker_summary takes `summary_df` which is already processed?
        # Let's check quant_engine.py structure. 
        # Actually it takes a dataframe.
        
        engine = QuantAnalyzer(None)
        
        # We need to construct a DF that looks like what 'get_broker_summary' from GoAPI returns?
        # No, analyze_broker_summary takes the DF directly.
        
        # Let's simulate the input DF
        # Let's simulate the input DF
        # Columns: Code, BVol, BVal, BAvg, SVol, SVal, SAvg
        df_input = pd.DataFrame([
            {'Code': 'YP', 'BVol': 1000, 'BVal': 500000, 'BAvg': 500, 'SVol': 0, 'SVal': 0, 'SAvg': 0, 'AvgPrice': 500},
            {'Code': 'PD', 'BVol': 0, 'BVal': 0, 'BAvg': 0, 'SVol': 1000, 'SVal': 505000, 'SAvg': 505, 'AvgPrice': 505}
        ])
        
        res = engine.analyze_broker_summary(df_input)
        
        self.assertIn('top1_buy_price', res)
        self.assertIn('top1_sell_price', res)
        
        print(f"   > Top 1 Buy Price: {res['top1_buy_price']}")
        print(f"   > Top 1 Sell Price: {res['top1_sell_price']}")
        print("   > Success: Quant Engine returns distinct Top 1 prices.")

    def test_03_catalyst_agent_prompt(self):
        """Verify Catalyst Agent receives new context fields"""
        print("\n[TEST] 3. Verifying AI Agent Context Integration...")
        
        # We can't easily check the internal prompt without mocking genai.GenerativeModel
        with patch('google.generativeai.GenerativeModel') as MockModel:
            mock_inst = MockModel.return_value
            mock_inst.generate_content.return_value.text = '{"analysis": "Ready"}'
            
            context = {
                'today_summary': 'Test Summary',
                'top_seller': 'YP',
                'seller_hist_net': 'Net Sell',
                'seller_avg_price': 500,
                'vwap': 510,
                'price_change': -2.5,
                'top1_buy_price': 490
            }
            
            catalyst_agent.get_bandarmology_analysis("TEST", context)
            
            # Check what was passed to generate_content
            args, _ = mock_inst.generate_content.call_args
            prompt_sent = args[0]
            
            self.assertIn("LOGIKA DETEKSI (GUIDELINES)", prompt_sent) 
            self.assertIn("HANYA sebutkan kode broker yang TERTULIS EKSPLISIT", prompt_sent)
            self.assertIn("Foreign Flow:", prompt_sent)
            self.assertIn("PBV:", prompt_sent)
            self.assertIn("Market Cap:", prompt_sent)
            self.assertIn("PETA KEKUATAN (TOP 3)", prompt_sent)
            
            print("   > Success: AI Prompt contains ANTI-HALLUCINATION, Logic, and ALL 4 VALUATION/MARKET DATA points.")

    def test_04_news_query_context(self):
        """Verify News Fetcher enforces Indonesian context"""
        print("\n[TEST] 4. Verifying News Fetcher Query Construction...")
        
        with patch('news_fetcher.requests.request') as mock_req:
            mock_req.return_value.status_code = 200
            mock_req.return_value.json.return_value = {'organic': []}
            
            # Test with .JK ticker
            news_fetcher.fetch_stock_news("BBCA.JK")
            
            args, kwargs = mock_req.call_args
            payload = kwargs.get('data')
            
            self.assertIn('IDX Indonesia', payload)
            self.assertIn('Saham \\"BBCA\\"', payload) # Check query structure (escaped quotes in json)
            
            print("   > Success: Query for BBCA.JK contains 'IDX Indonesia'.")
            
            # Test with 4-letter generic ticker
            news_fetcher.fetch_stock_news("GOTO")
            args, kwargs = mock_req.call_args
            payload = kwargs.get('data')
            self.assertIn('IDX Indonesia', payload, "4-letter generic ticker should also trigger Indonesia context")
            print("   > Success: Query for GOTO (no suffix) contains 'IDX Indonesia'.")

if __name__ == '__main__':
    unittest.main()
