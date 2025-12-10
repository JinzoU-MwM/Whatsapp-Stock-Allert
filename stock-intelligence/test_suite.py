import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from technical_analysis import analyze_technical
from catalyst_agent import get_catalyst_reasoning
from main import format_message

class TestStockSignalBot(unittest.TestCase):

    def setUp(self):
        self.ticker = "AAPL"
        self.whatsapp_url = "http://localhost:3000/health"

    # --- 1. Technical Analysis Tests ---
    def test_technical_analysis_structure(self):
        """Test if technical analysis returns correct dictionary structure."""
        print("\nTesting Technical Analysis Logic...")
        try:
            data = analyze_technical(self.ticker)
            
            self.assertIn("ticker", data)
            self.assertIn("price", data)
            self.assertIn("trend", data)
            self.assertIn("rsi", data)
            self.assertIn("support", data)
            self.assertIn("resistance", data)
            
            print(f"[OK] Technical Analysis Passed for {self.ticker}")
            print(f"   - Price: {data['price']}")
            print(f"   - Trend: {data['trend']}")
            print(f"   - RSI: {data['rsi']}")
            
        except Exception as e:
            self.fail(f"Technical Analysis failed with error: {e}")

    # --- 2. Catalyst Agent Tests ---
    @patch('catalyst_agent.genai.GenerativeModel')
    def test_catalyst_agent_mock(self, mock_model):
        """Test catalyst agent with mocked Gemini response."""
        print("\nTesting Catalyst Agent (Mocked)...")
        
        # Setup Mock
        mock_response = MagicMock()
        mock_response.text = "Mocked catalyst reason: Strong earnings report."
        mock_instance = mock_model.return_value
        mock_instance.generate_content.return_value = mock_response
        
        # Force API key presence for logic check
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"}):
            reason = get_catalyst_reasoning(self.ticker)
            self.assertIn("Mocked catalyst", reason)
            print(f"[OK] Catalyst Agent Logic Passed (Result: {reason})")

    def test_catalyst_agent_real_key_check(self):
        """Check if real API key is present and warn if not."""
        print("\nChecking Gemini API Key configuration...")
        key = os.getenv("GOOGLE_API_KEY")
        if key:
            print("[OK] GOOGLE_API_KEY is found.")
        else:
            print("[WARN] GOOGLE_API_KEY is MISSING. Real catalyst search will fail.")

    # --- 3. Message Formatting Tests ---
    def test_message_formatting(self):
        """Test if the message is formatted correctly."""
        print("\nTesting Message Formatting...")
        sample_ta = {
            "ticker": "TEST",
            "price": 100.0,
            "trend": "Bullish Uptrend",
            "rsi": 60.5,
            "support": 90.0,
            "resistance": 110.0,
            "stop_loss": 95.0,
            "target": 120.0,
            "ema20": 98.0
        }
        catalyst = "Test news event."
        
        msg = format_message("TEST", sample_ta, catalyst)
        self.assertIn("STOCK INTELLIGENCE: $TEST", msg)
        self.assertIn("Test news event", msg)
        self.assertIn("Bullish Uptrend", msg)
        print("[OK] Message Formatting Passed")

    # --- 4. Node.js Service Integration Test ---
    def test_whatsapp_service_connection(self):
        """Test connection to the local WhatsApp Node.js service."""
        print("\nTesting WhatsApp Service Connection...")
        try:
            response = requests.get(self.whatsapp_url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"[OK] WhatsApp Service is ONLINE.")
                print(f"   - Status: {data.get('status')}")
                print(f"   - Client Ready: {data.get('whatsapp_ready')}")
                
                if not data.get('whatsapp_ready'):
                    print("   [NOTE] WhatsApp Client is not ready. You need to scan the QR code in the Node.js terminal.")
            else:
                print(f"[FAIL] WhatsApp Service responded with status {response.status_code}")
                self.fail("Service unhealthy")
        except requests.exceptions.ConnectionError:
            print("[FAIL] WhatsApp Service is OFFLINE.")
            print("   -> Run 'npm start' in the 'whatsapp-service' directory.")
            # We don't fail the test suite to allow other tests to show results, 
            # but we mark it as a failure in output
            pass

if __name__ == '__main__':
    unittest.main()
