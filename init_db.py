import sqlite3

DB_PATH = "url_filter.db"  # Ensure this matches your main script

def init_db():
    """Create tables if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS blocked_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,  -- 'domain', 'hostname', or 'url_prefix'
            value TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS redirect_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,  -- 'domain', 'hostname', or 'url_prefix'
            value TEXT NOT NULL UNIQUE,
            proxy TEXT NOT NULL  -- Proxy URL for the redirect
        );

        CREATE TABLE IF NOT EXISTS tls_excluded_hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hostname TEXT NOT NULL UNIQUE
        );
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
