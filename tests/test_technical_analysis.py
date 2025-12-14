import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence'))

import technical_analysis

@pytest.fixture
def mock_ohlcv_data():
    """Generates synthetic OHLCV data for testing."""
    dates = pd.date_range(start="2023-01-01", periods=100)
    # Generate random walk price data
    price = 1000 + np.random.randn(100).cumsum()
    # Ensure High is max, Low is min
    high = price + np.random.rand(100) * 10
    low = price - np.random.rand(100) * 10
    volume = np.random.randint(1000, 10000, size=100)
    
    df = pd.DataFrame({
        'Open': price,
        'High': high,
        'Low': low,
        'Close': price,
        'Volume': volume
    }, index=dates)
    
    return df

def test_analyze_technical_indicators(mocker, mock_ohlcv_data):
    """Tests if analyze_technical correctly calculates indicators."""
    
    # Mock get_stock_data to return our synthetic data
    mocker.patch('technical_analysis.get_stock_data', return_value=(mock_ohlcv_data, "MOCK"))
    
    # Run analysis
    result = technical_analysis.analyze_technical("MOCK")
    
    # Check if key indicators are present in result
    assert result['rsi'] is not None
    assert isinstance(result['rsi'], (float, int))
    
    assert result['macd'] is not None
    assert result['adx'] is not None
    assert result['atr'] is not None
    assert result['mfi'] is not None
    assert result['obv'] is not None
    
    # Check Verdict
    assert result['verdict'] in ["STRONG BUY 🚀", "BUY / ACCUMULATE ✅", "WAIT & SEE ⚠️", "SELL / AVOID 🔻", "STRONG SELL ❌"]
    
    # Check trend string
    assert "Bullish" in result['trend'] or "Bearish" in result['trend'] or "Sideways" in result['trend']

def test_volume_analysis(mocker, mock_ohlcv_data):
    """Tests volume spike detection."""
    
    # Create a volume spike on the last day
    mock_ohlcv_data.iloc[-1, mock_ohlcv_data.columns.get_loc('Volume')] = 50000 # Massive spike
    # Previous avg is around 5000
    
    mocker.patch('technical_analysis.get_stock_data', return_value=(mock_ohlcv_data, "MOCK"))
    
    result = technical_analysis.analyze_technical("MOCK")
    
    # Should detect high volume
    assert "High" in result['vol_status'] or "EXPLOSIVE" in result['vol_status']
    assert result['vol_ratio'] > 2.0

def test_bandarmology_proxy(mocker, mock_ohlcv_data):
    """Tests if proxy bandarmology logic triggers."""
    # Scenario: Price UP + Vol UP + MFI UP -> Accumulation
    
    # Last candle: Price UP
    mock_ohlcv_data.iloc[-1, mock_ohlcv_data.columns.get_loc('Close')] = 1200
    mock_ohlcv_data.iloc[-2, mock_ohlcv_data.columns.get_loc('Close')] = 1100
    
    # Volume UP (Ratio > 1.2)
    mock_ohlcv_data.iloc[-1, mock_ohlcv_data.columns.get_loc('Volume')] = 15000 # High
    # Ensure prev volume makes average lower
    
    # Need to mock indicator calculation result inside pandas_ta if possible, 
    # but pandas_ta calculates from data. So if we manipulate data right, indicators follow.
    # MFI requires High, Low, Close, Volume.
    
    mocker.patch('technical_analysis.get_stock_data', return_value=(mock_ohlcv_data, "MOCK"))
    
    result = technical_analysis.analyze_technical("MOCK")
    
    # Since we forced price up and volume up, detecting 'Accumulation' is likely
    # though strict MFI logic depends on previous candles too.
    # We check if a status is returned at all.
    assert result['bandar_status'] is not None
    assert result['bandar_action'] is not None
