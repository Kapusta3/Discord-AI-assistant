import requests

import config

API_KEY = config.Gif_Token

def gif_search(query: str):
    url = "https://api.klipy.com/v2/search"

    query = f"{query}"
    print(f"[GIF_SEARCH Usage]: Searching gif with query: {query}")

    params = {
        "q": query,
        "key": API_KEY,
        "limit": 1
    }

    r = requests.get(url, params=params)
    data = r.json()
    try:
        return data["results"][0]["media_formats"]["gif"]["url"]
    except (KeyError, IndexError):
        return None