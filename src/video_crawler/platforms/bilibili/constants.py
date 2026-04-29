BASE_URL = "https://api.bilibili.com"

POPULAR_URL = "/x/web-interface/popular"
RANKING_URL = "/x/web-interface/ranking/v2"
SEARCH_URL = "/x/web-interface/search/type"
VIDEO_DETAIL_URL = "/x/web-interface/view"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

RANKING_CATEGORIES = {
    "all": 0,
    "animation": 1,
    "music": 3,
    "dance": 129,
    "game": 4,
    "knowledge": 36,
    "tech": 188,
    "sports": 234,
    "car": 223,
    "life": 160,
    "food": 211,
    "animal": 217,
    "fashion": 155,
    "entertainment": 5,
    "movie": 23,
    "tv": 11,
    "documentary": 177,
}
