import sqlite3

conn = sqlite3.connect("url_filter.db")
cursor = conn.cursor()

# Insert blocked entries
cursor.execute("INSERT INTO blocked_urls (type, value) VALUES ('domain', 'blocked.com')")
cursor.execute("INSERT INTO blocked_urls (type, value) VALUES ('hostname', 'www.example.com')")
cursor.execute("INSERT INTO blocked_urls (type, value) VALUES ('url_prefix', 'https://www.dhl.de/de/privatkunden/')")

# Insert redirect entries with custom proxies
cursor.execute("INSERT INTO redirect_urls (type, value, proxy) VALUES ('domain', 'whatismyip.com', 'http://proxy1.com:8080')")
cursor.execute("INSERT INTO redirect_urls (type, value, proxy) VALUES ('hostname', 'httpbin.org', 'http://proxy2.com:8080')")
cursor.execute("INSERT INTO redirect_urls (type, value, proxy) VALUES ('url_prefix', 'https://www.redirectme.com', 'http://proxy3.com:8080')")

# Insert TLS exclusions
cursor.execute("INSERT INTO tls_excluded_hosts (hostname) VALUES ('www.google.com')")

conn.commit()
conn.close()
