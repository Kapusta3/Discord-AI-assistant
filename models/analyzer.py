from openai import AsyncOpenAI
from config import SYSTEM_PROMPT_CHECKER, Analyzer_llm_name
from models.tool_router import tool_router

client = AsyncOpenAI(
    base_url="http://127.0.0.1:5614/v1",
    api_key="any"
)


async def analyzer(combined_text, chat_id, chat_history) -> str:
    if not combined_text.strip():
        return None

    lines = []
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "gpt"
        lines.append(f"{role}: {msg['content']}")

    context = "\n".join(lines) + f"\nuser (новое): {combined_text}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_CHECKER},
        {"role": "user", "content": context}
    ]

    response_obj = await client.chat.completions.create(
        model=Analyzer_llm_name,
        messages=messages,
        max_tokens=40
    )

    response = response_obj.choices[0].message.content
    print(f"[analyzer {chat_id}]: {response}")

    if "[IGNORE]" in response:
        return None

    result = await tool_router(combined_text, chat_history)
    print(f"[gpt {chat_id}]: {result}")

    return result