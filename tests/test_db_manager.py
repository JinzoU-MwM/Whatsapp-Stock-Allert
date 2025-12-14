import pytest
import sqlite3
import sys
import os
import tempfile

# Add the source directory to the path so we can import the module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'stock-intelligence'))

import db_manager

# Create a temporary file for the database
# We can't use :memory: easily because db_manager opens/closes connections internally
# creating separate in-memory DBs each time.
@pytest.fixture
def setup_db():
    """Initializes a temporary database file before each test."""
    # Create temp file
    fd, path = tempfile.mkstemp()
    os.close(fd) # Close file handle, we just need the path
    
    # Override global DB name
    original_db = db_manager.DB_NAME
    db_manager.DB_NAME = path
    
    # Init DB (create tables)
    db_manager.init_db()
    
    yield path
    
    # Teardown
    db_manager.DB_NAME = original_db
    if os.path.exists(path):
        os.remove(path)

def test_favorites(setup_db):
    # Test adding a favorite
    assert db_manager.add_favorite("BBCA") == True
    assert db_manager.is_favorite("BBCA") == True
    assert "BBCA" in db_manager.get_favorites()

    # Test removing a favorite
    db_manager.remove_favorite("BBCA")
    assert db_manager.is_favorite("BBCA") == False
    assert "BBCA" not in db_manager.get_favorites()

def test_portfolio(setup_db):
    # Test adding to portfolio
    assert db_manager.add_portfolio("TLKM", 3000, 10) == True
    
    portfolio = db_manager.get_portfolio()
    assert len(portfolio) == 1
    assert portfolio[0]['ticker'] == "TLKM"
    assert portfolio[0]['avg_price'] == 3000
    assert portfolio[0]['lots'] == 10

    # Test updating portfolio (Upsert)
    db_manager.add_portfolio("TLKM", 3500, 20)
    portfolio = db_manager.get_portfolio()
    assert len(portfolio) == 1
    assert portfolio[0]['avg_price'] == 3500
    assert portfolio[0]['lots'] == 20

    # Test deleting from portfolio
    assert db_manager.delete_portfolio("TLKM") == True
    assert len(db_manager.get_portfolio()) == 0

def test_history(setup_db):
    # Test adding history
    db_manager.add_history("ASII")
    db_manager.add_history("UNVR")
    
    history = db_manager.get_history(limit=5)
    assert "ASII" in history
    assert "UNVR" in history
    # Note: Order depends on timestamp, usually latest first.
    assert history[0] == "UNVR" # Most recent
    assert history[1] == "ASII"

def test_analysis_cache(setup_db):
    # Test saving analysis
    ta_data = {"rsi": 50, "macd": "bullish"}
    db_manager.save_analysis("GOTO", ta_data, "Buy", "Full Report")
    
    # Test retrieving cache
    cached = db_manager.get_cached_analysis("GOTO")
    assert cached is not None
    assert cached['ticker'] == "GOTO"
    assert cached['ta_data']['rsi'] == 50
    assert cached['ai_analysis'] == "Buy"
    
    # Test cache expiry (mocking time might be needed for strict test, but logic check is good enough)
    # For now, just ensure it returns data immediately after save.
