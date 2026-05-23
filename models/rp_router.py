import re
import emoji
from openai import AsyncOpenAI
from config import MAX_ATTEMPTS, RP_PROMPT, Rp_llm_name, Debug
from colorama import init, Fore

init(autoreset=True)

client = AsyncOpenAI(
    base_url="http://127.0.0.1:5614/v1",
    api_key="kapustiiik"
)

async def rp_router(text, chat_history, chat_info, tool_data="", attempt=0) -> str:
    dynamic_system_prompt = RP_PROMPT + f"\n\nОКРУЖЕНИЕ:\n{chat_info}"

    if attempt > 0:
        dynamic_system_prompt += "\n\nСИСТЕМНОЕ ПРЕДУПРЕЖДЕНИЕ: В ПРОШЛЫЙ РАЗ ТЫ СГЕНЕРИРОВАЛА ССЫЛКУ, ЭТО СТРОГО ЗАПРЕЩЕНО! ОТВЕТЬ ТЕКСТОМ БЕЗ ССЫЛОК."

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
        messages=messages
    )

    response = emoji.replace_emoji(response_obj.choices[0].message.content, replace='')

    response = re.sub(r'^(Милка|Milka|You|GPT|Assistant|Бот):\s*', '', response, flags=re.IGNORECASE).strip()

    response = re.split(r'\n(?=[A-Za-z0-9_а-яА-ЯёЁ \-\[\]]+:)', response)[0].strip()
    response = re.split(r'\n(?=\[?\d{2}:\d{2}\]?.*)', response)[0].strip()
    response = re.sub(r'\[.*?_RESULT\]:?\s*', '', response, flags=re.IGNORECASE)

    if tool_data == "" and re.search(r'https?://', response):
        if attempt < MAX_ATTEMPTS:
            if Debug:
                print(f"{Fore.YELLOW}[Attention]: Обнаружена сгаллюцинированная ссылка")
            return await rp_router(text, chat_history, chat_info, tool_data, attempt + 1)
        else:
            if Debug:
                print(f"{Fore.YELLOW}[Attention]: Превышен лимит перегенераций")
            response = re.sub(r'https?://\S+', '', response).strip()

    return response