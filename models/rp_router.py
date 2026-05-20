import re
import emoji
from openai import AsyncOpenAI
from config import *
from colorama import init, Fore

init(autoreset=True)

client = AsyncOpenAI(
    base_url="http://127.0.0.1:5614/v1",
    api_key="any"
)

async def rp_router(text, chat_history, chat_info, tool_data="") -> str:
    dynamic_system_prompt = SYSTEM_PROMPT_RESULTER + f"\n\nОКРУЖЕНИЕ:\n{chat_info}"

    if tool_data != "":
        dynamic_system_prompt += f"\n\nСкрытая информация для ответа:\n{tool_data}"

    messages = [
        {"role": "system", "content": dynamic_system_prompt},
        {"role": "user", "content": "Привет"},
        {"role": "assistant", "content": "привет"},
        {"role": "user", "content": "хз, ты предложи"},
        {"role": "assistant", "content": "не, мне впадлу думать"},
    ]

    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": text})

    response_obj = await client.chat.completions.create(
        model=Rp_llm_name,
        messages=messages,
        max_tokens=100
    )

    response = emoji.replace_emoji(response_obj.choices[0].message.content, replace='')

    response = re.sub(r'^(Милка|Milka|You|GPT|Assistant|Бот):\s*', '', response, flags=re.IGNORECASE).strip()

    response = re.split(r'\n(?=[A-Za-z0-9_а-яА-ЯёЁ \-\[\]]+:)', response)[0].strip()
    response = re.split(r'\n(?=\[?\d{2}:\d{2}\]?.*)', response)[0].strip()

    if tool_data == "" and re.search(r'https?://', response):
        print(f"{Fore.RED}Обнаружена сгаллюцинированная ссылка")
        response = re.sub(r'https?://\S+', '', response).strip()

    return response