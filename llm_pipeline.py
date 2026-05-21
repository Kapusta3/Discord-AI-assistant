import datetime
import database
from models.analyzer import analyzer
from models.tool_router import tool_router


async def process_message_chain(combined_text, chat_id, data):
    chat_history = await database.get_chat_history(chat_id, limit=8)
    user_rel = await database.get_user_relationship(data["user_id"])
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if data["chat_type"] == "DM":
        chat_info = f"Вы общаетесь в Личных Сообщениях (ЛС) наедине с пользователем {data['user_name']}."
    elif data["chat_type"] == "Group":
        chat_info = f"Вы находитесь в групповом чате (беседе). Название беседы/участники: '{data['chat_name']}'."
    else:
        chat_info = f"Вы находитесь на публичном сервере '{data['server_name']}', в канале '{data['chat_name']}'."

    chat_info += f"\nТвоё скрытое отношение к пользователю {data['user_name']}: {user_rel}"
    chat_info += f"\nТекущее системное время: {current_time}"

    should_reply, ratio = await analyzer(combined_text, chat_id, chat_history, chat_info)

    if ratio != 0.0:
        await database.queue_relationship_update(data["user_id"], ratio)

    if should_reply:
        response = await tool_router(combined_text, chat_history, chat_info)
        return response

    return None