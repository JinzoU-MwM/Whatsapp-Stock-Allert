import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_NAME = "stock_intelligence.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ta_data TEXT,
            ai_analysis TEXT,
            full_message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_cached_analysis(ticker, minutes_valid=120):
    """
    Retrieves cached analysis for a ticker if it's fresher than 'minutes_valid'.
    Default: 120 minutes (2 hours).
    Returns None if no valid cache found.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate cutoff time
    cutoff_time = datetime.now() - timedelta(minutes=minutes_valid)
    
    cursor.execute('''
        SELECT * FROM analysis_cache 
        WHERE ticker = ? AND timestamp > ?
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (ticker.upper(), cutoff_time))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "ticker": row["ticker"],
            "timestamp": row["timestamp"],
            "ta_data": json.loads(row["ta_data"]),
            "ai_analysis": row["ai_analysis"],
            "full_message": row["full_message"]
        }
    return None

def save_analysis(ticker, ta_data, ai_analysis, full_message):
    """
    Saves a new analysis result to the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO analysis_cache (ticker, timestamp, ta_data, ai_analysis, full_message)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        ticker.upper(), 
        datetime.now(), 
        json.dumps(ta_data, default=str), # Serialize dict to JSON string
        ai_analysis,
        full_message
    ))
    
    conn.commit()
    conn.close()
    print(f"Saved analysis for {ticker} to database.")
