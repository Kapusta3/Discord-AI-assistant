import base64

import aiohttp
from PIL import Image, ImageSequence
from io import BytesIO
import requests
from colorama import init, Fore
from config import Debug, DS_Token

init(autoreset=True)

# Чтоб норм открывались ссылки с discord
async def refresh_discord_url(url: str) -> str:
    if "discordapp.com" not in url and "discordapp.net" not in url:
        return url

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://discord.com/api/v10/attachments/refresh-urls",
            json={"attachment_urls": [url]},
            headers={"Authorization": DS_Token}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["refreshed_urls"][0]["refreshed"]
    return url

def pil_to_base64(img) -> str:
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def media_tool(source: str) -> list[str]:
    if Debug:
        print(f"{Fore.CYAN}[MEDIA_TOOL Usage]: Sending {source} to vision model.")

    if source.startswith("http"):
        response = requests.get(source)
        img = Image.open(BytesIO(response.content))
    else:
        img = Image.open(source)

    if not getattr(img, "is_animated", False):
        return [pil_to_base64(img.convert("RGB"))]

    frames = [frame.copy().convert("RGB") for frame in ImageSequence.Iterator(img)]
    return [pil_to_base64(frames[0]), pil_to_base64(frames[len(frames) // 2]), pil_to_base64(frames[-1])]