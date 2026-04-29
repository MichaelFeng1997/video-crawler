BASE_URL = "https://www.googleapis.com/youtube/v3"

VIDEOS_URL = "/videos"
SEARCH_URL = "/search"

VIDEO_PARTS = "snippet,contentDetails,statistics"
SEARCH_PARTS = "snippet"

DEFAULT_HEADERS: dict[str, str] = {}

RANKING_CATEGORIES = {
    "all": "0",
    "film": "1",
    "autos": "2",
    "music": "10",
    "pets": "15",
    "sports": "17",
    "gaming": "20",
    "people": "22",
    "comedy": "23",
    "entertainment": "24",
    "news": "25",
    "howto": "26",
    "education": "27",
    "science": "28",
}

CATEGORY_NAMES = {v: k for k, v in RANKING_CATEGORIES.items()}
