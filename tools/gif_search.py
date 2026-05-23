import requests
from config import Gif_Token, Debug
from colorama import init, Fore

init(autoreset=True)

def gif_search(query: str):
    url = "https://api.klipy.com/v2/search"

    query = f"{query}"

    if Debug:
        print(f"{Fore.CYAN}[GIF_SEARCH Usage]: Searching gif with query: {query}")

    params = {
        "q": query,
        "key": Gif_Token,
        "limit": 1
    }

    r = requests.get(url, params=params)
    data = r.json()
    try:
        return data["results"][0]["media_formats"]["gif"]["url"]
    except (KeyError, IndexError):
        return None