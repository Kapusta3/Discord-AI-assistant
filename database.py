import asyncio
import asyncpg
from colorama import Fore

db_pool = None
db_queue = asyncio.Queue()

async def init_db(db_url):
    global db_pool
    db_pool = await asyncpg.create_pool(db_url)
    asyncio.create_task(db_worker())

async def queue_message(data):
    await db_queue.put(data)

async def queue_relationship_update(user_id, ratio):
    await db_queue.put({
        "action": "update_relationship",
        "user_id": user_id,
        "ratio": ratio
    })

async def get_chat_history(chat_id, limit=8):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT m.message_text, m.is_bot, u.user_name, m.created_at 
            FROM messages m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.chat_id = $1 
            ORDER BY m.created_at DESC 
            LIMIT $2
        """, chat_id, limit)

    rows = list(reversed(rows))
    history = []
    for row in rows:
        time_str = row['created_at'].strftime("%H:%M")
        if row['is_bot']:
            history.append({"role": "assistant", "content": row['message_text']})
        else:
            history.append({"role": "user", "content": f"[Автор: {row['user_name']} | {time_str}]\n{row['message_text']}"})

    return history

async def get_user_relationship(user_id):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT user_relationship FROM users WHERE user_id = $1", user_id)
        return round(row["user_relationship"], 2) if row else 0.0

async def db_worker():
    while True:
        data = await db_queue.get()
        async with db_pool.acquire() as conn:
            try:
                if data.get("action") == "update_relationship":
                    await conn.execute("""
                        UPDATE users SET user_relationship = user_relationship + $1 WHERE user_id = $2
                    """, data["ratio"], data["user_id"])
                else:
                    if data.get("server_name"):
                        await conn.execute("""
                            INSERT INTO servers (server_id, server_name) VALUES ($1, $2)
                            ON CONFLICT (server_id) DO NOTHING
                        """, data["server_id"], data["server_name"])

                    await conn.execute("""
                        INSERT INTO users (user_id, user_tag, user_name) VALUES ($1, $2, $3)
                        ON CONFLICT (user_id) DO NOTHING
                    """, data["user_id"], data["user_tag"], data["user_name"])

                    server_id = data["server_id"] if data.get("server_name") else None
                    await conn.execute("""
                        INSERT INTO chats (chat_id, chat_name, chat_type, server_id) VALUES ($1, $2, $3, $4)
                        ON CONFLICT (chat_id) DO NOTHING
                    """, data["chat_id"], data["chat_name"], data["chat_type"], server_id)

                    await conn.execute("""
                        INSERT INTO messages (message_id, chat_id, user_id, message_text, is_bot)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (message_id) DO NOTHING
                    """, data["message_id"], data["chat_id"], data["user_id"], data["message_text"], data.get("is_bot", False))

            except Exception as e:
                print(f"{Fore.RED}[DB Error]: {e}")

        db_queue.task_done()

async def flush_queue():
    await db_queue.join()