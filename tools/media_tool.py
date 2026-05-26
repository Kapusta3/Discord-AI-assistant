import base64
import aiohttp
from PIL import Image, ImageSequence
from io import BytesIO
import requests
from colorama import init, Fore
from config import Debug, DS_Token
import re

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


import subprocess
import tempfile
import os


def extract_video_frames(source: str) -> list[str]:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            frame_path = os.path.join(tmpdir, "frame_%d.png")
            # 3 кадра из видеео
            subprocess.run([
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                source
            ], capture_output=True, text=True)

            result = subprocess.run([
                "ffmpeg", "-i", source,
                "-vf", "select='eq(n\\,0)+eq(n\\,50)+eq(n\\,100)'",
                "-vsync", "vfr",
                "-frames:v", "3",
                frame_path
            ], capture_output=True, timeout=15)

            frames = []
            for i in range(1, 4):
                path = os.path.join(tmpdir, f"frame_{i}.png")
                if os.path.exists(path):
                    img = Image.open(path).convert("RGB")
                    frames.append(pil_to_base64(img))

            return frames
    except Exception as e:
        print(f"{Fore.RED}[FFMPEG Error]: {e}")
        return []

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

def pil_to_base64(img) -> str:
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def media_tool(source: str) -> list[str]:
    if Debug:
        print(f"{Fore.CYAN}[MEDIA_TOOL Usage]: Sending {source} to vision model.")

    if "tenor.com/view/" in source:
        source = resolve_tenor_url(source)

    if source.split("?")[0].endswith(".mp4"):
        return extract_video_frames(source)

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        if source.startswith("http"):
            response = requests.get(source, headers=headers, timeout=10)
            img = Image.open(BytesIO(response.content))
        else:
            img = Image.open(source)
    except Exception as e:
        print(f"{Fore.RED}[MEDIA_TOOL Error]: {e}")
        return []

    print(f"Frames count: {getattr(img, 'n_frames', 1)}, is_animated: {getattr(img, 'is_animated', False)}")

    if not getattr(img, "is_animated", False):
        return [pil_to_base64(img.convert("RGB"))]

    frames = [frame.copy().convert("RGB") for frame in ImageSequence.Iterator(img)]
    return [pil_to_base64(frames[0]), pil_to_base64(frames[len(frames) // 2]), pil_to_base64(frames[-1])]