import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add support for import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence'))

from technical_analysis import get_valuation_data

def test_valuation_zero_per_low_pbv(mocker):
    """Test case: PER is 0 (or missing), PBV is 0.5 (Cheap). Should be Undervalued."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        'trailingPE': 0, 
        'forwardPE': 0, 
        'priceToBook': 0.5,
        'returnOnEquity': 0.05,
        'marketCap': 1000000000
    }
    
    with patch('yfinance.Ticker', return_value=mock_ticker):
        data = get_valuation_data("BSBK")
        print(f"\nResult: {data}")
        assert data['valuation_status'] != "N/A", "Status should not be N/A for valid PBV"
        assert "Undervalued" in data['valuation_status'], "Should be marked Undervalued based on PBV"

def test_valuation_negative_per_high_pbv(mocker):
    """Test case: PER is negative (Loss), PBV is 5.0 (Expensive). Should be Overvalued."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        'trailingPE': -5.0, 
        'forwardPE': -5.0, 
        'priceToBook': 5.0,
        'returnOnEquity': -0.1,
    }
    
    with patch('yfinance.Ticker', return_value=mock_ticker):
        data = get_valuation_data("GOTO")
        print(f"\nResult: {data}")
        assert data['valuation_status'] != "N/A"
        assert "Overvalued" in data['valuation_status']

def test_valuation_normal_undervalued(mocker):
    """Standard case: PER 5, PBV 0.8."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        'trailingPE': 5.0, 
        'priceToBook': 0.8
    }
    with patch('yfinance.Ticker', return_value=mock_ticker):
        data = get_valuation_data("BBRI")
        assert "Undervalued" in data['valuation_status']

def test_valuation_garbage_pbv_correction(mocker):
    """Test case: PBV is 99999 (Garbage) but Calculated PBV (Price/Book) is reasonable."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        'trailingPE': 10.0,
        'priceToBook': 99999.99, # Garbage
        'bookValue': 100.0,
        'currentPrice': 200.0,   # Actual PBV should be 2.0
    }
    with patch('yfinance.Ticker', return_value=mock_ticker):
        data = get_valuation_data("ERR")
        print(f"\nGarbage Data Result: {data}")
        # Expect it to correct to 2.0
        assert data['pbv'] == 2.0
        assert data['valuation_status'] == "Fair Value"

def test_valuation_currency_mismatch_bumi(mocker):
    """Test case: BUMI case (Price in IDR, Book Value in USD)."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        'trailingPE': 0.0,
        'priceToBook': 88999.0, # Raw garbage
        'bookValue': 0.004,     # USD value (~65 IDR)
        'currentPrice': 356.0,  # IDR value
    }
    with patch('yfinance.Ticker', return_value=mock_ticker):
        data = get_valuation_data("BUMI.JK")
        print(f"\nBUMI Data Result: {data}")
        # Expect PBV to be ~5.4 (356 / (0.004 * 16400))
        # 0.004 * 16400 = 65.6
        # 356 / 65.6 = 5.42
        assert 5.0 < data['pbv'] < 6.0
        assert "Overvalued" in data['valuation_status']
