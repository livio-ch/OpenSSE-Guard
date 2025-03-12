import sqlite3

conn = sqlite3.connect("url_filter.db")
cursor = conn.cursor()

# Insert blocked entries
cursor.execute("INSERT INTO blocked_urls (type, value) VALUES ('domain', 'blocked.com')")
cursor.execute("INSERT INTO blocked_urls (type, value) VALUES ('domain', 'blockedsite.com')")
cursor.execute("INSERT INTO blocked_urls (type, value) VALUES ('hostname', 'www.example.com')")
cursor.execute("INSERT INTO blocked_urls (type, value) VALUES ('url_prefix', 'https://www.dhl.de/de/privatkunden/')")

# Insert redirect entries with custom proxies
cursor.execute("INSERT INTO redirect_urls (type, value, proxy) VALUES ('domain', 'whatismyip.com', 'http://localhost:8081')")
cursor.execute("INSERT INTO redirect_urls (type, value, proxy) VALUES ('hostname', 'httpbin.org', 'http://localhost:8081')")
cursor.execute("INSERT INTO redirect_urls (type, value, proxy) VALUES ('url_prefix', 'https://www.redirectme.com', 'http://localhost:8081')")

# Insert TLS exclusions
cursor.execute("INSERT INTO tls_excluded_hosts (hostname) VALUES ('www.google.com')")

conn.commit()
conn.close()
