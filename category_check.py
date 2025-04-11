import requests
from bs4 import BeautifulSoup
import cache  # Import your cache module


CATEGORY_MAP = {
    "72": {"name": "Academic Fraud", "action": "blocked"},
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
    "19": {"name": "Movies", "action": "allowed"},
    "50": {"name": "Music", "action": "allowed"},
    "33": {"name": "News/Media", "action": "allowed"},
    "69": {"name": "Non-Profits", "action": "allowed"},
    "20": {"name": "P2P/File sharing", "action": "blocked"},
    "57": {"name": "Parked Domains", "action": "blocked"},
    "48": {"name": "Photo Sharing", "action": "allowed"},
    "71": {"name": "Podcasts", "action": "allowed"},
    "66": {"name": "Politics", "action": "allowed"},
    "21": {"name": "Portals", "action": "allowed"},
    "22": {"name": "Radio", "action": "allowed"},
    "65": {"name": "Religious", "action": "allowed"},
    "54": {"name": "Research/Reference", "action": "allowed"},
    "23": {"name": "Search Engines", "action": "allowed"},
    "24": {"name": "Social Networking", "action": "allowed"},
    "47": {"name": "Software/Technology", "action": "allowed"},
    "51": {"name": "Sports", "action": "allowed"},
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

def check_category_action(domain):
    url = f"https://domain.opendns.com/{domain}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    cached_response = cache.get_cache(url)
    if  cached_response:
        result= cached_response
    else:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            return {"error": str(e)}

        soup = BeautifulSoup(response.text, 'html.parser')
        result = {
            "domain": domain,
            "categories": [],
            "action": None
        }

        for b_tag in soup.find_all("b"):
            if b_tag.get("id", "").startswith("catname-"):
                cat_id = b_tag.get("id").split("-")[-1]
                parent_td = b_tag.find_parent("td")
                next_td = parent_td.find_next_sibling("td") if parent_td else None

                if next_td and "Approved" in next_td.text:
                    cat_info = CATEGORY_MAP.get(cat_id, None)
                    if cat_info:
                        category_name = cat_info["name"]
                        category_action = cat_info["action"]
                        result["categories"].append({
                            "category_name": category_name,
                            "action": category_action
                        })
        cache.set_cache(url,result)
    # Check if any category is blocked


    for category in result["categories"]:
        if category["action"] == "blocked":
            return {'status': 'blocked', 'message': f"Domain belongs to blocked category: {category['category_name']}"}

    return None  # Not blocked
