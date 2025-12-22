
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Setup Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_controller import StockAppController

class TestCIOIntegration(unittest.TestCase):
    
    @patch('app_controller.get_technical_analysis')
    @patch('app_controller.get_bandarmology_analysis')
    @patch('app_controller.get_fundamental_analysis')
    @patch('app_controller.get_final_verdict')
    @patch('app_controller.analyze_technical')
    @patch('app_controller.fetch_stock_news')
    def test_run_analysis_cio_flow(self, mock_news, mock_ta, mock_cio, mock_fund, mock_bandar, mock_tech):
        print("\n[TEST] Verifying CIO Agent Integration in App Controller...")
        
        # 1. Setup Mocks
        controller = StockAppController()
        
        # Tech Data Mock
        mock_ta.return_value = {
            'ticker': 'TEST', 'price': 1000, 'trend': 'Bullish', 
            'macd_status': 'Netral', 'vol_status': 'Normal', 'vol_ratio': 1.0,
            'rsi': 50, 'support': 900, 'resistance': 1100,
            'valuation': {'per': 10, 'pbv': 1, 'roe': 15, 'der': 0.5, 'eps_growth': 10}
        }
        
        # AI Agent Mocks
        mock_tech.return_value = {'analysis': 'Tech Good', 'trading_plan': {'buy_area': '950'}}
        mock_bandar.return_value = {'status': 'AKUMULASI', 'analysis': 'Bandar Good'}
        mock_fund.return_value = {'valuation_status': 'UNDERVALUED', 'analysis': 'Fund Good'}
        
        # CIO Mock (The Target)
        mock_cio.return_value = {
            'final_score': 85,
            'recommended_action': 'STRONG BUY',
            'primary_strategy': 'SWING',
            'allocation_size': 'AGGRESSIVE',
            'final_reasoning': 'All indicators align perfectly.'
        }
        
        # News Mock
        mock_news.return_value = "News Summary"
        
        # 2. Run Analysis
        # We need to mock QuantEngine too or it will try to access DB/API
        controller.quant_engine = MagicMock()
        controller.quant_engine.fetch_real_bandarmology.return_value = None # Skip bandar data processing for simplicity
        
        msg, chart, score = controller.run_analysis('TEST')
        
        # 3. Assertions
        print(f"   > Final Score: {score}")
        print(f"   > Message Snippet:\n{msg[:200]}...")
        
        self.assertIn("CIO NOTE", msg)
        self.assertIn("STRATEGY: SWING", msg)
        self.assertIn("Alloc: AGGRESSIVE", msg)
        self.assertIn("VERDICT: STRONG BUY", msg)
        
        # Verify CIO was called with correct data
        args, _ = mock_cio.call_args
        self.assertEqual(args[0], 'TEST') # Ticker
        self.assertEqual(args[3]['valuation_status'], 'UNDERVALUED') # Fund Res
        
        print("   > Success: CIO Agent was called and output is in the message.")

if __name__ == '__main__':
    unittest.main()
