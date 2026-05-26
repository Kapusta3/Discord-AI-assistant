import re

import requests


def resolve_tenor_url(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        matches = re.findall(r'https://media[0-9]*\.tenor\.com/[^"\']+\.gif', response.text)
        if matches:
            return matches[0]
    except Exception as e:
        print(f"[TENOR Error]: {e}")
    return url

print(resolve_tenor_url("https://tenor.com/ru/view/blm-gif-25815938"))