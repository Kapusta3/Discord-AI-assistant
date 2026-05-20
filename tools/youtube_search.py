from youtube_search import YoutubeSearch
import socket


def youtube_search(query: str) -> str:
    try:
        print(f"[YOUTUBE_SEARCH Usage]: Searching video with query: {query}")

        socket.setdefaulttimeout(15)

        results = YoutubeSearch(query, max_results=1).to_dict()

        if not results:
            return "ничего не нашлось"

        video_id = results[0]["id"]
        return f"https://youtube.com/watch?v={video_id}"

    except Exception as e:
        print(f"[youtube error] {e}")
        return "ничего не нашлось"

    finally:
        socket.setdefaulttimeout(None)