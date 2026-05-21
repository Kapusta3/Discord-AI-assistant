import asyncio
import random
import discord
from colorama import init, Fore

from config import DS_Token, DB_URL, MAX_BUFFER_SIZE, DELAY_SECONDS
from schemas import AgentRequest
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
        print(f"{Fore.RED}[SYNC Error]: {e}")


async def trigger_llm(chat_id, request: AgentRequest, channel):
    await sync_offline_messages(channel)
    await database.flush_queue()

    texts_list = unprocessed_texts.pop(chat_id, [])
    if not texts_list:
        return

    if chat_id in chat_timers:
        del chat_timers[chat_id]

    combined_text = "\n".join(texts_list)
    print(f"\nЧат {chat_id}:\n{combined_text}\n")

    try:
        async with channel.typing():
            agent_response = await process_message_chain(combined_text, request)

        if agent_response and agent_response.should_reply and agent_response.messages:
            print(f"{Fore.GREEN}[gpt in {chat_id}]: {agent_response.messages}")

            for i, part in enumerate(agent_response.messages):
                if i > 0:
                    delay = min(max(len(part) / random.uniform(4.0, 7.0) + 1.5, 2.0), 8.0)
                    async with channel.typing():
                        await asyncio.sleep(delay)

                sent_msg = await channel.send(part)

                bot_data = request.to_dict()
                bot_data.update({
                    "message_id": sent_msg.id,
                    "message_text": part,
                    "user_id": client.user.id,
                    "user_tag": client.user.name,
                    "user_name": "Milka",
                    "is_bot": True
                })
                await database.queue_message(bot_data)

    except Exception as e:
        print(f"{Fore.RED}[LLM Error]: {e}")

# ну че, таймер говно
async def delayed_trigger(chat_id, request, channel):
    try:
        await asyncio.sleep(DELAY_SECONDS)
        await trigger_llm(chat_id, request, channel)
    except asyncio.CancelledError:
        pass


@client.event
async def on_ready():
    await database.init_db(DB_URL)
    print(f"{Fore.BLUE}[LOG]: Logged in as {client.user}, database connected.")


@client.event
async def on_message(message):
    if message.author == client.user or not message.content.strip():
        return

    # Записи для данных также в говно
    if message.guild:
        chat_type, chat_name = "Guild", message.channel.name
        server_id, server_name = message.guild.id, message.guild.name
        env_info = f"Публичный сервер '{server_name}', канал '{chat_name}'."
    elif message.channel.type == discord.ChannelType.group:
        chat_type = "Group"
        chat_name = f"Group with {', '.join(u.name for u in message.channel.recipients)}"
        server_id, server_name = None, None
        env_info = f"Групповой чат (беседа). Название/участники: '{chat_name}'."
    else:
        chat_type, chat_name = "DM", f"DM with {message.author}"
        server_id, server_name = None, None
        env_info = f"Личные Сообщения (ЛС) наедине с пользователем {message.author.display_name}."

    chat_id = message.channel.id

    request = AgentRequest(
        user_id=message.author.id,
        user_tag=message.author.name,
        user_name=message.author.display_name,
        message_id=message.id,
        message_text=message.content,
        chat_id=chat_id,
        chat_name=chat_name,
        chat_type=chat_type,
        server_id=server_id,
        server_name=server_name,
        is_bot=False,
        environment_info=env_info
    )

    await database.queue_message(request.to_dict())

    unprocessed_texts.setdefault(chat_id, []).append(f"[Автор: {message.author.display_name}]\n{message.content}")

    if chat_id in chat_timers:
        chat_timers[chat_id].cancel()

    if len(unprocessed_texts[chat_id]) >= MAX_BUFFER_SIZE:
        print(f"[Timer]: Буфер {chat_id} переполнен")
        asyncio.create_task(trigger_llm(chat_id, request, message.channel))
    else:
        chat_timers[chat_id] = asyncio.create_task(delayed_trigger(chat_id, request, message.channel))


client.run(DS_Token)