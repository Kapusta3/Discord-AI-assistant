from ddgs import DDGS
from colorama import init, Fore

init(autoreset=True)

def web_search(query: str, max_results: int = 10) -> str:
    print(f"{Fore.CYAN}[WEB_SEARCH Usage]: Searching info with query: {query}")
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)

        if not results:
            return "ничего не нашлось"

        output = ""
        for r in results:
            output += f"Title: {r['title']}\n"
            output += f"Snippet: {r['body']}\n"
            output += f"URL: {r['href']}\n\n"

        return output