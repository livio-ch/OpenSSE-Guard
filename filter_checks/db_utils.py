import sqlite3
import logging

DB_PATH = "url_filter.db"  # Achtung: Wenn du mehrere Pfade brauchst, ggf. dynamisch machen

def query_database(query, params=()):
    """
    Führt eine SQL-Abfrage auf der SQLite-Datenbank aus und gibt das erste Ergebnis zurück.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return None
