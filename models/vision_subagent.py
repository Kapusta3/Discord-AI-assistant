from openai import AsyncOpenAI
from config import Vision_llm_name, Debug, VISION_SUBAGENT_PROMPT
from colorama import init, Fore

init(autoreset=True)

client = AsyncOpenAI(
    base_url="http://127.0.0.1:5614/v1",
    api_key="kapustiiik"
)

async def vision_subagent(frames: list[str], prompt: str) -> str:
    content = [{"type": "text", "text": prompt}]

    for frame in frames:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{frame}"}
        })

    messages = [
        {"role": "system", "content": VISION_SUBAGENT_PROMPT},
        {"role": "user", "content": content}
    ]

    response_obj = await client.chat.completions.create(
        model=Vision_llm_name,
        messages=messages
    )

    response = response_obj.choices[0].message.content

    if Debug:
        print(f"{Fore.CYAN}[vision_subagent]: {response}")

    return response
