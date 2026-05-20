import json
from openai import AsyncOpenAI
from models.rp_router import rp_router
from tools.get_current_time import get_current_time
from tools.gif_search import gif_search
from tools.web_search import web_search
from tools.youtube_search import youtube_search
from config import Tool_llm_name

client = AsyncOpenAI(
    base_url="http://127.0.0.1:5614/v1",
    api_key="lm-studio"
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
            "name": "youtube_search",
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
    }
]

async def tool_router(user_input, chat_history, chat_info) -> str:
    messages = [
        {"role": "system",
         "content": "Ты диспетчер функций. Твоя единственная задача — вызывать функции ТОЛЬКО если пользователь прямо просит об этом (найти видео, гифку, узнать время). Если пользователь просто общается (пишет 'привет', 'да', 'тоже', 'как дела') — НИЧЕГО НЕ ДЕЛАЙ, просто ответь текстом."},
        {"role": "user", "content": user_input}
    ]

    response = await client.chat.completions.create(
        model=Tool_llm_name,
        messages=messages,
        tools=tools_schema,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    collected_tool_data = ""

    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            if function_name not in available_functions:
                continue

            function_to_call = available_functions[function_name]
            try:
                function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            except json.JSONDecodeError:
                function_args = {}

            function_response = function_to_call(**function_args)
            collected_tool_data += f"[{function_name.upper()}_RESULT]: {function_response}\n"

        # Передаем chat_info в RP-роутер!
        return await rp_router(user_input, chat_history, chat_info, tool_data=collected_tool_data)

    else:
        return await rp_router(user_input, chat_history, chat_info, tool_data="")
