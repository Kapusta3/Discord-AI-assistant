import json
from openai import AsyncOpenAI
from models.rp_router import rp_router
from models.vision_subagent import vision_subagent
from tools.get_current_time import get_current_time
from tools.gif_search import gif_search
from tools.media_tool import media_tool, refresh_discord_url
from tools.web_search import web_search
from tools.youtube_search_tool import youtube_search
from config import Tool_llm_name, TOOL_ROUTER_PROMPT, Debug
from colorama import init, Fore

init(autoreset=True)

client = AsyncOpenAI(
    base_url="http://127.0.0.1:5614/v1",
    api_key="kapustiiik"
)

available_functions = {
    "get_current_time": get_current_time,
    "web_search": web_search,
    "youtube_search": youtube_search,
    "gif_search": gif_search,
}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Получить текущее время и дату."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Искать информацию в интернете.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос, например 'погода в Москве'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_search_tool",
            "description": "Искать видео или песню на YouTube.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Название или тема видео"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gif_search",
            "description": "Искать смешные или подходящие по смыслу GIF анимации.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Тематика гифки на английском, например 'cat funny'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "media_tool",
            "description": "Смотреть на медиафайлы пользователя.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Ссылка на медиа, что отправил пользователь."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

async def tool_router(user_input, chat_history, chat_info) -> str:
    collected_tool_data = ""
    processed_urls = set()

    for line in user_input.splitlines():
        if line.startswith("[MEDIA]:"):
            url = line.replace("[MEDIA]:", "").strip()

            if url in processed_urls:
                continue
            processed_urls.add(url)

            url = await refresh_discord_url(url)
            frames = media_tool(url)
            if not frames:
                collected_tool_data += "[MEDIA_TOOL_RESULT]: Не удалось загрузить медиафайл."
                continue
            result = await vision_subagent(frames, "Опиши что на этом медиафайле.")
            collected_tool_data += f"[MEDIA_TOOL_RESULT]: {result}\n"

    messages = [
        {"role": "system", "content": TOOL_ROUTER_PROMPT},
        {"role": "user", "content": user_input}
    ]

    response = await client.chat.completions.create(
        model=Tool_llm_name,
        messages=messages,
        tools=tools_schema,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

            if function_name == "media_tool":
                url = await refresh_discord_url(function_args.get("query", ""))
                frames = media_tool(url)
                if not frames:
                    collected_tool_data += "[MEDIA_TOOL_RESULT]: Не удалось загрузить медиафайл.\n"
                    continue
                result = await vision_subagent(frames, "Опиши что на этом медиафайле.")
                collected_tool_data += f"[MEDIA_TOOL_RESULT]: {result}\n"
                continue

            if function_name not in available_functions:
                continue

            function_to_call = available_functions[function_name]
            function_response = function_to_call(**function_args)
            collected_tool_data += f"[{function_name.upper()}_RESULT]: {function_response}\n"

    if Debug:
        print(f"{Fore.CYAN}[tool_router]: collected_tool_data = {collected_tool_data}")

    if not collected_tool_data:
        print(f"{Fore.BLUE}[LOG]: Тулзы не использовались")

    return await rp_router(user_input, chat_history, chat_info, tool_data=collected_tool_data)