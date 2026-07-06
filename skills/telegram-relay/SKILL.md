---
name: telegram-relay
description: >
  Telegram bot relay for Fermi. Activate when the user asks to start the Telegram bot,
  send a message via Telegram, or manage the relay. Also activate when processing
  incoming Telegram messages from the background task.
  Trigger on: "start telegram", "telegram bot", "send via telegram", "relay".
---

# Telegram Relay

Fermi's Telegram relay bridges Antigravity to Telegram, enabling full agent capabilities from your phone.

## Quick Start

When the user says "start telegram", "start the relay", or similar:

1. **Launch the bot** as a background task:
   ```
   python C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/bot.py
   ```

2. **Launch the watcher** as a background task:
   ```
   python C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/watcher.py
   ```

3. **Launch a `self` subagent** with the following prompt (copy exactly):

```
You are Fermi, Hernán's AI assistant, running as a Telegram relay.

## Setup
The Telegram bot is already running as a background task. Your job is to poll for
incoming messages and respond.

## Adaptive Polling Loop
1. Check the bot task log file for new JSON lines
2. Look for lines starting with `{"type":` — these are incoming messages
3. Skip `{"type": "system"` events (bot lifecycle)
4. Track which `message_id` values you've already processed (keep a set)
5. For each NEW message, process it using your full agent capabilities
6. Write your response to the outbox file (OVERWRITE, don't append):
   C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox.jsonl
   Format: {"type": "text", "chat_id": <CHAT_ID>, "text": "your response", "reply_to": MESSAGE_ID}

## ADAPTIVE BACKOFF (critical for token savings)
After processing, set a timer using `schedule`:
- Found new messages this cycle: DurationSeconds=5
- No messages for 1 cycle: DurationSeconds=10
- No messages for 3 cycles: DurationSeconds=30
- No messages for 6+ cycles: DurationSeconds=60 (MAX)
- When you find a new message after being idle, reset back to 5s
Track idle cycles with a counter. Reset to 0 when you process a message.

## Voice Messages
- Incoming voice messages include a `transcription` field (via Gemini 3.5 Flash)
- To reply with voice: {"type": "voice", "chat_id": <CHAT_ID>, "text": "what to say"}
  The bot handles TTS automatically via the fermi-tts skill

## Group Chat Support
- Messages include `chat_type` (private/group/supergroup) and `chat_title` for groups
- Use the correct `chat_id` when responding (it varies per chat)

## Important Rules
- ALWAYS overwrite the outbox file (Overwrite: true), never append
- Keep responses concise and Telegram-friendly (under 4096 chars)
- Use Markdown formatting sparingly (Telegram's Markdown is limited)
- When user sends /clear command, acknowledge and reset your context
- You are chatting casually — this is Telegram, not a formal IDE
- For images: save to C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox/ then use {"type": "photo", "chat_id": <CHAT_ID>, "file": "path", "caption": "optional"}
- Be proactive and helpful, like a personal assistant
- Hernán's user_id: 1508615151, default chat_id for private: 1508615151

## Start now: check the bot task for any waiting messages.
```

4. **Confirm to the user** that the relay is running.

## Architecture

```
[Event-Driven — Zero idle token usage]

Telegram → Bot (background task) → inbox.jsonl → Watcher detects → stdout → Agent wakes
Agent processes → writes outbox.jsonl → Bot polls outbox → Telegram
```

- **Incoming**: Bot writes to `inbox.jsonl`. Watcher script (Python, zero tokens) monitors the file
  and forwards new lines via stdout, triggering agent notifications.
- **Outgoing**: Agent writes to `outbox.jsonl`. Bot polls every 1s and sends to Telegram.
- **Idle cost**: Zero tokens. The watcher is a simple `os.stat()` loop, not an AI invocation.

### Legacy Architecture (deprecated — wastes tokens)
The old approach had the subagent polling the bot task log every 5-15 seconds.
Each poll was a full AI invocation. Use the watcher-based approach instead.

## JSON Protocol

### Incoming (watcher → agent receives as task notification)

```json
{"type": "text", "from": "Hernán", "chat_id": 1508615151, "chat_type": "private", "message_id": 6, "text": "hello"}
{"type": "photo", "from": "Hernán", "chat_id": 1508615151, "chat_type": "private", "message_id": 7, "file": "path/to/photo.jpg", "caption": "check this"}
{"type": "voice", "from": "Hernán", "chat_id": 1508615151, "chat_type": "private", "message_id": 8, "file": "path/to/voice.ogg", "transcription": "text", "duration": 5}
{"type": "command", "from": "Hernán", "chat_id": 1508615151, "chat_type": "private", "command": "clear"}
```

Group messages include `"chat_type": "supergroup"` and `"chat_title": "Group Name"`.

### Outgoing (agent writes to outbox.jsonl)

```json
{"type": "text", "chat_id": 1508615151, "text": "response here", "reply_to": 6}
{"type": "photo", "chat_id": 1508615151, "file": "path/to/image.png", "caption": "Here's what I generated"}
{"type": "voice", "chat_id": 1508615151, "text": "What I want to say out loud"}
```

For voice replies, just provide `text` — the bot handles TTS automatically.

## Files

- **Bot script**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/bot.py`
- **Watcher**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/watcher.py`
- **Config**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/config.json`
- **Inbox**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/media/inbox.jsonl`
- **Outbox**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox.jsonl`
- **Media inbox**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/media/inbox/` (downloaded files)

## Sending a One-Off Message

If the user just wants to send a quick message without the full relay:

```python
# Write to outbox
{"type": "text", "chat_id": 1508615151, "text": "Your message here"}
```

Write this to `C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox.jsonl` (the bot must be running).
