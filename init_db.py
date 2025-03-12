import sqlite3

DB_PATH = "url_filter.db"  # Ensure this matches your main script

def init_db():
    """Clear the database and create tables if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing entries from tables (optional: you can drop tables if you prefer)
    cursor.execute("DELETE FROM blocked_urls")  # Clear all records from blocked_urls
    cursor.execute("DELETE FROM redirect_urls")  # Clear all records from redirect_urls
    cursor.execute("DELETE FROM tls_excluded_hosts")  # Clear all records from tls_excluded_hosts

    # You can also drop the tables entirely if you want to re-create them
    # cursor.execute("DROP TABLE IF EXISTS blocked_urls")
    # cursor.execute("DROP TABLE IF EXISTS redirect_urls")
    # cursor.execute("DROP TABLE IF EXISTS tls_excluded_hosts")

    # Create tables if they don't exist
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
