import asyncio
import discord
import asyncpg
from config import DS_Token, DB_URL, MAX_BUFFER_SIZE, DELAY_SECONDS
from models.analyzer import analyzer
from colorama import init, Fore

from models.tool_router import tool_router

init(autoreset=True)

client = discord.Client(status=discord.Status.dnd)
db_queue = asyncio.Queue()
db_pool = None

chat_timers = {}
unprocessed_texts = {}

async def db_worker():
    while True:
        data = await db_queue.get()
        async with db_pool.acquire() as conn:
            try:
                if data.get("action") == "update_relationship":
                    await conn.execute("""
                        UPDATE users 
                        SET user_relationship = user_relationship + $1 
                        WHERE user_id = $2
                    """, data["ratio"], data["user_id"])

                else:
                    if data.get("server_name"):
                        await conn.execute("""
                            INSERT INTO servers (server_id, server_name)
                            VALUES ($1, $2)
                            ON CONFLICT (server_id) DO NOTHING
                        """, data["server_id"], data["server_name"])

                    await conn.execute("""
                        INSERT INTO users (user_id, user_tag, user_name)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id) DO NOTHING
                    """, data["user_id"], data["user_tag"], data["user_name"])

                    server_id = data["server_id"] if data.get("server_name") else None
                    await conn.execute("""
                        INSERT INTO chats (chat_id, chat_name, chat_type, server_id)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (chat_id) DO NOTHING
                    """, data["chat_id"], data["chat_name"], data["chat_type"], server_id)

                    await conn.execute("""
                        INSERT INTO messages (message_id, chat_id, user_id, message_text, is_bot)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (message_id) DO NOTHING
                    """, data["message_id"], data["chat_id"], data["user_id"], data["message_text"],
                                       data.get("is_bot", False))

                    role = "BOT" if data.get("is_bot") else "USER"

            except Exception as e:
                print(f"{Fore.RED}[DB Error]: {e}")

        db_queue.task_done()


async def get_chat_history(chat_id, limit=8):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT m.message_text, m.is_bot, u.user_name 
            FROM messages m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.chat_id = $1 
            ORDER BY m.created_at DESC 
            LIMIT $2
        """, chat_id, limit)

    rows = list(reversed(rows))
    history = []
    for row in rows:
        if row['is_bot']:
            history.append({"role": "assistant", "content": row['message_text']})
        else:
            history.append({"role": "user", "content": f"{row['user_name']}: {row['message_text']}"})

    return history


async def trigger_llm(chat_id, data):
    texts_list = unprocessed_texts.pop(chat_id, [])
    if not texts_list:
        return

    if chat_id in chat_timers:
        del chat_timers[chat_id]

    combined_text = "\n".join(texts_list)
    print(f"\nЧат {chat_id}:\n{combined_text}\n") #так красивее

    chat_history = await get_chat_history(chat_id, limit=8)

    try:
        async with db_pool.acquire() as conn:
            rel_row = await conn.fetchrow("SELECT user_relationship FROM users WHERE user_id = $1", data["user_id"])
            user_rel = round(rel_row["user_relationship"], 2) if rel_row else 0.0

        if data["chat_type"] == "DM":
            chat_info = f"Вы общаетесь в Личных Сообщениях (ЛС) наедине с пользователем {data['user_name']}."
        elif data["chat_type"] == "Group":
            chat_info = f"Вы находитесь в групповом чате (беседе). Название беседы/участники: '{data['chat_name']}'."
        else:
            chat_info = f"Вы находитесь на публичном сервере '{data['server_name']}', в канале '{data['chat_name']}'."

        chat_info += f"\nТвоё скрытое отношение к пользователю {data['user_name']}: {user_rel}"

        should_reply, ratio = await analyzer(combined_text, chat_id, chat_history, chat_info)

        if ratio != 0.0:
            await db_queue.put({
                "action": "update_relationship",
                "user_id": data["user_id"],
                "ratio": ratio
            })

        if should_reply:
            channel = client.get_channel(chat_id)
            async with channel.typing():
                response = await tool_router(combined_text, chat_history, chat_info)

            if response:
                print(f"{Fore.GREEN}[gpt in {chat_id}]: {response}")
                import random

                # реалистичный перенос строк
                message_parts = [part.strip() for part in response.split('\n') if part.strip()]

                for i, part in enumerate(message_parts):
                    if i > 0:
                        typing_speed = random.uniform(4.0, 7.0) #че с инета взял скорость среднюю, ну медленно
                        delay = len(part) / typing_speed + 2

                        async with channel.typing():
                            await asyncio.sleep(delay)

                    sent_msg = await channel.send(part)

                    bot_data = data.copy()
                    bot_data["message_id"] = sent_msg.id
                    bot_data["message_text"] = part
                    bot_data["user_id"] = client.user.id
                    bot_data["user_tag"] = client.user.name
                    bot_data["user_name"] = "Milka"
                    bot_data["is_bot"] = True

                    await db_queue.put(bot_data)

    except Exception as e:
        print(f"{Fore.RED}[LLM Error]: {e}")


@client.event
async def on_ready():
    global db_pool
    db_pool = await asyncpg.create_pool(DB_URL)
    print(f"{Fore.BLUE}[LOG]: Logged in as {client.user}, database connected.")
    asyncio.create_task(db_worker())


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.strip():
        return

    chat_type = "Guild" if message.guild else "DM"
    chat_name = message.channel.name if message.guild else f"DM with {message.author}"
    server_name = message.guild.name if message.guild else None
    server_id = message.guild.id if message.guild else None
    chat_id = message.channel.id

    data = {
        "user_id": message.author.id,
        "user_tag": message.author.name,
        "user_name": message.author.display_name,
        "message_id": message.id,
        "message_text": message.content,
        "chat_id": chat_id,
        "chat_name": chat_name,
        "chat_type": chat_type,
        "server_id": server_id,
        "server_name": server_name,
        "is_bot": False
    }

    await db_queue.put(data)

    if chat_id not in unprocessed_texts:
        unprocessed_texts[chat_id] = []

    unprocessed_texts[chat_id].append(f"{message.author.display_name}: {message.content}")

    if chat_id in chat_timers:
        chat_timers[chat_id].cancel()

    if len(unprocessed_texts[chat_id]) >= MAX_BUFFER_SIZE:
        print(f"[Timer]: Буфер {chat_id} переполнен")
        asyncio.create_task(trigger_llm(chat_id, data))
    else:
        async def wait_and_trigger():
            try:
                await asyncio.sleep(DELAY_SECONDS)
                await trigger_llm(chat_id, data)
            except asyncio.CancelledError:
                pass

        chat_timers[chat_id] = asyncio.create_task(wait_and_trigger())


client.run(DS_Token)