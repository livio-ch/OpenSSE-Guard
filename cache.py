import sqlite3
import time
import logging
import json
import threading

# Constants
DB_PATH = "cache.db"
CACHE_TTL = 3600  # 1 hour

# Thread lock for safe access in multi-threaded environments
lock = threading.Lock()

def create_cache_db():
    """Create the cache table if it doesn't exist."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    response TEXT,
                    timestamp REAL
                )
            """)
            conn.commit()
    except Exception:
        logging.exception("Error creating cache table")

# Ensure cache table is created on module import
create_cache_db()

def set_cache(key, data):
    """Store data in the cache with a timestamp."""
    try:
        timestamp = int(time.time())

        with lock, sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache (key, response, timestamp)
                VALUES (?, ?, ?)
            """, (key, json.dumps(data), timestamp))
            conn.commit()
    except Exception:
        logging.exception(f"Error saving key '{key}' to cache")

def get_cache(key):
    """Retrieve data from the cache."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT response, timestamp FROM cache WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()

        if row:
            data = row[0]  # The first value is the serialized data (string)
            timestamp = row[1]

            # Check if the cached data has expired based on TTL
            if time.time() - timestamp > CACHE_TTL:
                logging.info(f"Cache for key '{key}' has expired.")
                return None  # Data has expired

            # Check if the data is already a dictionary (not a string)
            if isinstance(data, dict):
                return data  # If it's already a dict, return it directly
            else:
                return json.loads(data)  # Otherwise, deserialize the JSON string
        return None  # No cache entry found
    except Exception as e:
        logging.error(f"Error retrieving from cache: {e}")
        return None


def get_all_cache():
    """Retrieve all cache entries."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT key, response, timestamp FROM cache")
        rows = c.fetchall()
        conn.close()

        # Convert rows into a list of dictionaries
        all_cache = []
        for row in rows:
            key, data, timestamp = row
            # Check if the data is already a dictionary (not a string)
            if isinstance(data, dict):
                all_cache.append({key: data})
            else:
                all_cache.append({key: json.loads(data)})
        return all_cache
    except Exception as e:
        logging.error(f"Error retrieving all cache entries: {e}")
        return []
