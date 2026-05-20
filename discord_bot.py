import asyncio
import discord
import asyncpg
from config import DS_Token, DB_URL, MAX_BUFFER_SIZE, DELAY_SECONDS
from models.analyzer import analyzer
from colorama import init, Fore

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
                print(f"{Fore.RED}[DB ERROR] {e}")

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
    print(f"\n{data['user_name']} в {chat_id}:\n{combined_text}\n")

    chat_history = await get_chat_history(chat_id, limit=8)

    try:
        async with client.get_channel(chat_id).typing():

            if data["chat_type"] == "DM":
                chat_info = f"Вы общаетесь в Личных Сообщениях (DM) с пользователем {data['user_name']}."
            else:
                chat_info = f"Вы находитесь на сервере '{data['server_name']}', в канале '{data['chat_name']}'."

            response = await analyzer(combined_text, chat_id, chat_history, chat_info)

        if response:
            channel = client.get_channel(chat_id)
            sent_msg = await channel.send(response)

            bot_data = data.copy()
            bot_data["message_id"] = sent_msg.id
            bot_data["message_text"] = response
            bot_data["user_id"] = client.user.id
            bot_data["user_tag"] = client.user.name
            bot_data["user_name"] = "Milka"
            bot_data["is_bot"] = True

            await db_queue.put(bot_data)

    except Exception as e:
        print(f"{Fore.RED}[LLM ERROR] {e}")


@client.event
async def on_ready():
    global db_pool
    db_pool = await asyncpg.create_pool(DB_URL)
    print(f"Logged in as {client.user}, database connected.")
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
        "user_id": message.author.id, "user_tag": message.author.name, "user_name": message.author.display_name,
        "message_id": message.id, "message_text": message.content, "chat_id": chat_id,
        "chat_name": chat_name, "chat_type": chat_type, "server_id": server_id, "server_name": server_name,
        "is_bot": False
    }

    await db_queue.put(data)

    if chat_id not in unprocessed_texts:
        unprocessed_texts[chat_id] = []

    unprocessed_texts[chat_id].append(f"{message.author.display_name}: {message.content}")

    if chat_id in chat_timers:
        chat_timers[chat_id].cancel()

    if len(unprocessed_texts[chat_id]) >= MAX_BUFFER_SIZE:
        print(f"[ТАЙМЕР] Буфер {chat_id} переполнен")
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