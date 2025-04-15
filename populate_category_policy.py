import sqlite3

DB_PATH = "url_filter.db"

CATEGORY_MAP = {
    "72": {"name": "Academic Fraud", "action": "blocked"},
    "58" :{"name": "Adult Themes", "action": "blocked"},
    "53": {"name": "Advertising", "action": "allowed"},
    "2": {"name": "Alcohol", "action": "blocked"},
    "76": {"name": "Anime/Manga/Webcomic", "action": "allowed"},
    "3": {"name": "Auctions", "action": "allowed"},
    "70": {"name": "Automotive", "action": "allowed"},
    "4": {"name": "Blogs", "action": "blocked"},
    "56": {"name": "Business Services", "action": "allowed"},
    "5": {"name": "Chat", "action": "blocked"},
    "6": {"name": "Classifieds", "action": "allowed"},
    "7": {"name": "Dating", "action": "blocked"},
    "8": {"name": "Drugs", "action": "blocked"},
    "9": {"name": "Ecommerce/Shopping", "action": "allowed"},
    "52": {"name": "Educational Institutions", "action": "allowed"},
    "10": {"name": "File Storage", "action": "blocked"},
    "55": {"name": "Financial Institutions", "action": "allowed"},
    "67": {"name": "Forums/Message boards", "action": "blocked"},
    "11": {"name": "Gambling", "action": "blocked"},
    "12": {"name": "Games", "action": "allowed"},
    "49": {"name": "Government", "action": "allowed"},
    "13": {"name": "Hate/Discrimination", "action": "blocked"},
    "14": {"name": "Health and Fitness", "action": "allowed"},
    "15": {"name": "Humor", "action": "allowed"},
    "16": {"name": "Instant Messaging", "action": "blocked"},
    "17": {"name": "Jobs/Employment", "action": "allowed"},
    "60": {"name": "Lingerie/Bikini", "action": "blocked"},
    "19": {"name": "Movies", "action": "allowed"},
    "50": {"name": "Music", "action": "allowed"},
    "33": {"name": "News/Media", "action": "allowed"},
    "69": {"name": "Non-Profits", "action": "allowed"},
    "63": {"name": "Nudity", "action": "blocked"},
    "20": {"name": "P2P/File sharing", "action": "blocked"},
    "57": {"name": "Parked Domains", "action": "blocked"},
    "48": {"name": "Photo Sharing", "action": "allowed"},
    "71": {"name": "Podcasts", "action": "allowed"},
    "66": {"name": "Politics", "action": "allowed"},
    "64": {"name": "Pornography", "action": "allowed"},
    "21": {"name": "Portals", "action": "allowed"},
    "61": {"name": "Proxy/Anonymizer", "action": "allowed"},
    "22": {"name": "Radio", "action": "allowed"},
    "65": {"name": "Religious", "action": "allowed"},
    "54": {"name": "Research/Reference", "action": "allowed"},
    "23": {"name": "Search Engines", "action": "allowed"},
    "62": {"name": "Sexuality", "action": "allowed"},
    "24": {"name": "Social Networking", "action": "allowed"},
    "47": {"name": "Software/Technology", "action": "allowed"},
    "51": {"name": "Sports", "action": "allowed"},
    "59": {"name": "Tasteless", "action": "allowed"},
    "34": {"name": "Television", "action": "allowed"},
    "73": {"name": "Tobacco", "action": "blocked"},
    "68": {"name": "Travel", "action": "allowed"},
    "170": {"name": "URL Shorteners", "action": "blocked"},
    "26": {"name": "Video Sharing", "action": "allowed"},
    "27": {"name": "Visual Search Engines", "action": "allowed"},
    "28": {"name": "Weapons", "action": "blocked"},
    "77": {"name": "Web Spam", "action": "blocked"},
    "29": {"name": "Webmail", "action": "allowed"}
}

def populate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM category_policy")  # optional: clear before inserting

    for cat_id, data in CATEGORY_MAP.items():
        cursor.execute(
            "INSERT INTO category_policy (category_id, name, action) VALUES (?, ?, ?)",
            (cat_id, data["name"], data["action"])
        )

    conn.commit()
    conn.close()
    print("Category policy table populated successfully.")

if __name__ == "__main__":
    populate()
