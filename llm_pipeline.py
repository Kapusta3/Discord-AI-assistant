import datetime
import database
from schemas import AgentRequest, AgentResponse
from models.analyzer import analyzer
from models.tool_router import tool_router

async def process_message_chain(combined_text: str, request: AgentRequest) -> AgentResponse:
    chat_history = await database.get_chat_history(request.chat_id, limit=8)
    user_rel = await database.get_user_relationship(request.user_id)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    chat_info = request.environment_info
    chat_info += f"\nТвоё скрытое отношение к пользователю {request.user_name}: {user_rel}"
    chat_info += f"\nТекущее системное время: {current_time}"

    should_reply, ratio = await analyzer(combined_text, request.chat_id, chat_history, chat_info)

    if ratio != 0.0:
        await database.queue_relationship_update(request.user_id, ratio)

    if should_reply:
        response_text = await tool_router(combined_text, chat_history, chat_info)
        if response_text:
            message_parts = [part.strip() for part in response_text.split('\n') if part.strip()]
            return AgentResponse(should_reply=True, messages=message_parts)

    return AgentResponse(should_reply=False, messages=[])