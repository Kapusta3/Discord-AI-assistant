import asyncio
import discord
import random
from config import DS_Token, DB_URL, MAX_BUFFER_SIZE, DELAY_SECONDS
from colorama import init, Fore

import database
from llm_pipeline import process_message_chain

init(autoreset=True)

client = discord.Client(status=discord.Status.dnd)
chat_timers = {}
unprocessed_texts = {}


async def sync_offline_messages(channel):
    try:
        async for msg in channel.history(limit=10):
            if not msg.content.strip():
                continue

            await database.queue_message({
                "user_id": msg.author.id,
                "user_tag": msg.author.name,
                "user_name": msg.author.display_name,
                "message_id": msg.id,
                "message_text": msg.content,
                "chat_id": channel.id,
                "chat_name": channel.name if msg.guild else f"DM with {msg.author}",
                "chat_type": "Guild" if msg.guild else "DM",
                "server_id": msg.guild.id if msg.guild else None,
                "server_name": msg.guild.name if msg.guild else None,
                "is_bot": msg.author.id == client.user.id
            })
    except Exception as e:
        print(f"{Fore.RED}[SYNC Error]: Не удалось синхронизировать сообщения: {e}")


async def trigger_llm(chat_id, data):
    channel = client.get_channel(chat_id)
    await sync_offline_messages(channel)
    await asyncio.sleep(0.5)

    texts_list = unprocessed_texts.pop(chat_id, [])
    if not texts_list:
        return

    if chat_id in chat_timers:
        del chat_timers[chat_id]

    combined_text = "\n".join(texts_list)
    print(f"\nЧат {chat_id}:\n{combined_text}\n")

    try:
        async with channel.typing():
            response = await process_message_chain(combined_text, chat_id, data)

        if response:
            print(f"{Fore.GREEN}[gpt in {chat_id}]: {response}")

            message_parts = [part.strip() for part in response.split('\n') if part.strip()]

            for i, part in enumerate(message_parts):
                if i > 0:
                    typing_speed = random.uniform(4.0, 7.0)
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

                await database.queue_message(bot_data)

    except Exception as e:
        print(f"{Fore.RED}[LLM Error]: {e}")


@client.event
async def on_ready():
    await database.init_db(DB_URL)
    print(f"{Fore.BLUE}[LOG]: Logged in as {client.user}, database connected.")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.strip():
        return

    chat_type = None
    chat_name = None
    server_name = None
    server_id = None

    if message.guild is None:
        if message.channel.type == discord.ChannelType.private:
            chat_type = "DM"
            chat_name = f"DM with {message.author}"
        elif message.channel.type == discord.ChannelType.group:
            chat_type = "Group"
            users = [user.name for user in message.channel.recipients]
            chat_name = f"Group with {', '.join(users)}"
    else:
        chat_type = "Guild"
        chat_name = message.channel.name
        server_name = message.guild.name
        server_id = message.guild.id

    chat_id = message.channel.id

    data = {
        "user_id": message.author.id, "user_tag": message.author.name, "user_name": message.author.display_name,
        "message_id": message.id, "message_text": message.content, "chat_id": chat_id,
        "chat_name": chat_name, "chat_type": chat_type, "server_id": server_id, "server_name": server_name,
        "is_bot": False
    }

    await database.queue_message(data)

    if chat_id not in unprocessed_texts:
        unprocessed_texts[chat_id] = []

    unprocessed_texts[chat_id].append(f"[Автор: {message.author.display_name}]\n{message.content}")

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