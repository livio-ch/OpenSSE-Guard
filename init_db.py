import sqlite3

DB_PATH = "url_filter.db"  # Ensure this matches your main script

def init_db():
    """Clear the database and create tables if they do not exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()



    # Create tables if they don't exist
    cursor.executescript('''
            DROP TABLE IF EXISTS blocked_urls;
            DROP TABLE IF EXISTS redirect_urls;
            DROP TABLE IF EXISTS tls_excluded_hosts;
            DROP TABLE IF EXISTS blocked_files;
            DROP TABLE IF EXISTS blocked_mimetypes;


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
        CREATE TABLE IF NOT EXISTS blocked_files (
            file_hash TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS blocked_mimetypes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS category_policy (
            category_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            action TEXT NOT NULL  -- 'allowed' or 'blocked'
        );

    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
