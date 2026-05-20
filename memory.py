class ShortMemory:
    memory = []

def add2short_memory(user_message, agent_message):
    ShortMemory.memory.append({"role": "user", "content": user_message})
    ShortMemory.memory.append({"role": "assistant", "content": agent_message})


def get_context_for_checker(current_text: str, max_iterations: int = 5) -> str:
    recent = ShortMemory.memory[-(max_iterations * 2):]

    lines = []
    for msg in recent:
        role = "user" if msg["role"] == "user" else "gpt"
        lines.append(f"{role}: {msg['content']}")

    lines.append(f"user: {current_text}")

    return "\n".join(lines)