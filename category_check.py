import requests
from bs4 import BeautifulSoup
import cache
from filter_checks.db_utils import  load_category_policy

# ✅ Load the current category policy from the database
CATEGORY_MAP = load_category_policy()


def check_category_action(domain, user_id="default"):
    url = f"https://domain.opendns.com/{domain}"
    headers = {"User-Agent": "Mozilla/5.0"}

    # ✅ Check if the category names are cached
    cached_categories = cache.get_cache(url)
    if cached_categories:
        categories = cached_categories
    else:
        # ✅ Fetch and parse OpenDNS category page
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            return {"error": str(e)}

        soup = BeautifulSoup(response.text, 'html.parser')
        categories = []

        for b_tag in soup.find_all("b"):
            if b_tag.get("id", "").startswith("catname-"):
                cat_id = b_tag.get("id").split("-")[-1]
                parent_td = b_tag.find_parent("td")
                next_td = parent_td.find_next_sibling("td") if parent_td else None

                if next_td and "Approved" in next_td.text:
                    cat_info = CATEGORY_MAP.get(cat_id)
                    if cat_info:
                        category_name = cat_info["name"]
                        action = cat_info["action"]


                        # ✅ Save only category name to cache
                        categories.append(category_name)

        cache.set_cache(url, categories)

    # ✅ Evaluate latest action from DB mapping every time (even if category was cached)
    for category in categories:
        for cat_id, info in CATEGORY_MAP.items():
            if info["name"] == category and info["action"] == "blocked":
                return {
                    'status': 'blocked',
                    'message': f"Domain belongs to blocked category: {category}"
                }

    return None  # Not blocked
