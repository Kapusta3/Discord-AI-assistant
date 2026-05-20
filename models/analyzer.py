import re
from openai import AsyncOpenAI
from config import ANALYZER_PROMPT, Analyzer_llm_name
from colorama import init, Fore

init(autoreset=True)

client = AsyncOpenAI(
    base_url="http://127.0.0.1:5614/v1",
    api_key="any"
)

async def analyzer(combined_text, chat_id, chat_history, chat_info):
    if not combined_text.strip():
        return False, 0.0

    lines = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "gpt"
        lines.append(f"{role}: {msg['content']}")

    context = "\n".join(lines) + f"\nuser (новое): {combined_text}"

    messages = [
        {"role": "system", "content": ANALYZER_PROMPT},
        {"role": "user", "content": context}
    ]

    response_obj = await client.chat.completions.create(
        model=Analyzer_llm_name,
        messages=messages,
        max_tokens=40
    )

    response = response_obj.choices[0].message.content
    print(f"{Fore.BLUE}[analyzer {chat_id}]: {response}")

    ratio = 0.0
    match = re.search(r'\[([+-]?\d+(?:\.\d+)?)\]', response)
    if match:
        try:
            ratio = float(match.group(1))
        except ValueError:
            pass

    if "[IGNORE]" in response:
        return False, ratio

    return True, ratio