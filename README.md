<div align="center">

![Discord AI Assistant](img/git-reame.png)

**A self-hosted Discord AI agent with memory, vision, and tool use.**

![Python](https://img.shields.io/badge/Python-3.11+-3572A5?style=flat-square&logo=python&logoColor=white)
![Discord](https://img.shields.io/badge/Discord-selfbot-5865F2?style=flat-square&logo=discord&logoColor=white)
![LM Studio](https://img.shields.io/badge/LM%20Studio-local%20LLM-FF6B35?style=flat-square)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?style=flat-square&logo=postgresql&logoColor=white)

</div>

---

## What is this

A Discord AI agent that runs entirely on local LLMs via LM Studio. It sits in your chats, reads the conversation, decides whether to respond, and does so in a human-like way — with memory of past messages, awareness of who it's talking to, and access to tools.

No cloud APIs. No OpenAI bills. Runs on your machine.

---

## Architecture

The pipeline is a chain of specialized models, each doing one job:

```
Discord message
      │
      ▼
 [ Analyzer ]  ──── Should we even reply? What's the tone shift?
      │
      ▼
 [ Tool Router ]  ── Does this need a tool? (search, gif, time, vision...)
      │
      ├── web_search      → DuckDuckGo / search engine
      ├── gif_search      → Tenor API
      ├── youtube_search  → YouTube
      ├── get_current_time
      └── media_tool      → downloads media → vision model → text description
      │
      ▼
 [ RP Router ]  ───── Generates the actual response
      │
      ▼
 Discord reply
```

Every model is a separate LM Studio instance — you can swap any of them independently.

---

## Features

- **Multi-model pipeline** — analyzer, tool router, vision subagent, and RP model run as separate stages
- **Vision** — when someone sends an image or GIF, the agent actually looks at it before responding. GIFs are sampled at 3 keyframes (first, middle, last)
- **Persistent memory** — full chat history stored in PostgreSQL via asyncpg
- **Relationship tracking** — per-user attitude score that shifts based on interactions and influences response tone
- **Message buffering** — collects multiple messages before triggering a response, like a real person reading a chat
- **Tool use** — web search, YouTube, GIFs, current time, media analysis
- **Discord CDN handling** — automatically refreshes expired attachment URLs before processing

---

## Stack

| Component | Tech |
|---|---|
| Discord | `discord.py` (selfbot) |
| LLM inference | LM Studio (OpenAI-compatible API) |
| Database | PostgreSQL + `asyncpg` |
| Vision | PIL + base64 → vision LLM |
| HTTP | `aiohttp` + `requests` |

---

## Setup

**1. Clone**
```bash
git clone https://github.com/Kapusta3/Discord-AI-assistant
cd Discord-AI-assistant
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure `.env`**
```env
DS_TOKEN=your_discord_token
DB_URL=postgresql://user:password@localhost/dbname
GIF_TOKEN=your_tenor_api_key
```

**4. Start LM Studio** and load your models. Update `config.py` with the model names and ports you're using.

**5. Run**
```bash
python discord_bot.py
```

---

## Configuration

Key settings in `config.py`:

```python
DELAY_SECONDS = 7        # how long to wait before responding
MAX_BUFFER_SIZE = 5      # max messages to batch before forcing a response

Analyzer_llm_name = "..."
Rp_llm_name = "..."
Vision_llm_name = "..."
Tool_llm_name = "..."
```

---

## Notes

- This is a **selfbot** — it runs on a real user account, not a bot token. Use at your own risk; this violates Discord's ToS.
- All LLM inference is local. You need a machine capable of running the models you choose.
- Vision works best with models that support image input (e.g. LLaVA-based, Qwen-VL, etc.)

---

<div align="center">
<sub>Built for local use. No data leaves your machine.</sub>
</div>
