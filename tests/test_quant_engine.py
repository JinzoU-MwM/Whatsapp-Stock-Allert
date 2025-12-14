import pytest
import pandas as pd
import sys
import os

# Add path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence'))

from quant_engine import QuantAnalyzer

@pytest.fixture
def quant_engine():
    return QuantAnalyzer(goapi_client=None)

def test_analyze_broker_summary_accumulation(quant_engine):
    # Mock Transaction Data (Accumulation Scenario)
    # Broker AK (Institution) buying heavily
    data = pd.DataFrame([
        {'Broker': 'AK', 'Action': 'BUY', 'Volume': 5000, 'AvgPrice': 1000},
        {'Broker': 'BK', 'Action': 'BUY', 'Volume': 3000, 'AvgPrice': 1005},
        {'Broker': 'ZP', 'Action': 'BUY', 'Volume': 2000, 'AvgPrice': 1002},
        {'Broker': 'YP', 'Action': 'SELL', 'Volume': 2000, 'AvgPrice': 995},
        {'Broker': 'PD', 'Action': 'SELL', 'Volume': 2000, 'AvgPrice': 990},
    ])
    
    result = quant_engine.analyze_broker_summary(data)
    
    # Check if detected as accumulation
    assert "ACCUMULATION" in result['status'] or "Akumulasi" in result['status']
    assert result['bandar_score'] > 0
    assert result['top_buyer'] == 'AK'
    assert result['buyer_type'] == 'Institusi/Market Maker'
    assert result['net_vol_ratio'] > 1.5 # 10000 / 4000 = 2.5

def test_analyze_broker_summary_distribution(quant_engine):
    # Mock Transaction Data (Distribution Scenario)
    # Retail brokers buying (YP), Institution selling (AK)
    data = pd.DataFrame([
        {'Broker': 'YP', 'Action': 'BUY', 'Volume': 2000, 'AvgPrice': 1000},
        {'Broker': 'AK', 'Action': 'SELL', 'Volume': 5000, 'AvgPrice': 1005},
        {'Broker': 'BK', 'Action': 'SELL', 'Volume': 3000, 'AvgPrice': 1002},
    ])
    
    result = quant_engine.analyze_broker_summary(data)
    
    # Check distribution
    assert result['bandar_score'] < 0
    assert result['net_vol_ratio'] < 0.6

def test_analyze_foreign_flow(quant_engine):
    # Mock Foreign Data
    data = pd.DataFrame({
        'Date': pd.date_range(start='2023-01-01', periods=5),
        'NetForeignBuy': [100, 200, -50, 300, 500] # Mostly positive
    })
    
    result = quant_engine.analyze_foreign_flow(data)
    
    # Since 5 days sum is > 0, and current day is > 0, it hits "Foreign Inflow"
    # AND since 20 days (or all data if <20) sum is > 0, it upgrades to "Strong Foreign Accumulation"
    assert "Strong Foreign Accumulation" in result['status']
    assert result['foreign_score'] > 0
    assert result['net_1d'] == 500
    assert result['net_5d'] > 0

def test_calculate_dynamic_risk(quant_engine):
    entry = 1000
    atr = 50
    
    risk = quant_engine.calculate_dynamic_risk(entry, atr, method="aggressive")
    
    # Aggressive: 1.5x ATR SL, 2.5x ATR TP
    expected_sl = 1000 - (1.5 * 50) # 925
    expected_tp = 1000 + (2.5 * 50) # 1125
    
    assert risk['stop_loss'] == 925
    assert risk['target_price'] == 1125

def test_calculate_final_verdict(quant_engine):
    # Strong Buy Case
    res = quant_engine.calculate_final_verdict(
        tech_score=90,
        bandar_score=50, # Norm -> 100
        foreign_score=20, # Norm -> 80
        sentiment_score=80
    )
    
    # Weighted: (90*0.4) + (100*0.3) + (80*0.15) + (80*0.15) = 36 + 30 + 12 + 12 = 90
    assert res['final_score'] >= 85
    assert "STRONG BUY" in res['verdict']
