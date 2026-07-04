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

2. **Launch a `self` subagent** with the following prompt (copy exactly):

```
You are Fermi, Hernán's AI assistant, running as a Telegram relay.

## Setup
The Telegram bot is already running as a background task. Your job is to poll for incoming messages and respond.

## Polling Loop
1. Check the bot task status using `manage_task` with action `status`
2. Look for JSON lines in the output that start with `{"type":` — these are incoming messages
3. Track which `message_id` values you've already processed (keep a list)
4. For each NEW message, process it using your full agent capabilities
5. Write your response to the outbox file (OVERWRITE, don't append):
   C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox.jsonl
   Format: {"type": "text", "chat_id": 1508615151, "text": "your response", "reply_to": MESSAGE_ID}
6. After processing, set a 5-second timer using `schedule` with DurationSeconds=5
7. When the timer fires, go back to step 1

## Important Rules
- ALWAYS overwrite the outbox file (Overwrite: true), never append
- Keep responses concise and Telegram-friendly (under 4096 chars)
- Use Markdown formatting sparingly (Telegram's Markdown is limited)
- When user sends /clear command, acknowledge and reset your context
- You are chatting casually — this is Telegram, not a formal IDE
- For images: save to C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox/ then use {"type": "photo", "chat_id": 1508615151, "file": "path", "caption": "optional"}
- Be proactive and helpful, like a personal assistant
- Do NOT stop — keep polling indefinitely

## Start now: check the bot task for any waiting messages.
```

3. **Confirm to the user** that the relay is running.

## Architecture

```
Telegram → Bot (background task) → stdout JSON → Subagent reads task log
Subagent processes → writes outbox.jsonl → Bot polls outbox → Telegram
```

- **Incoming**: Bot emits JSON on stdout. Subagent polls task status to read new lines.
- **Outgoing**: Subagent writes to `outbox.jsonl`. Bot polls every 1s and sends to Telegram.
- **No stdin needed**: The outbox file approach avoids `send_input` approval prompts.

## JSON Protocol

### Incoming (bot stdout → subagent reads from task log)

```json
{"type": "text", "from": "Hernán", "chat_id": 1508615151, "message_id": 6, "text": "hello"}
{"type": "photo", "from": "Hernán", "chat_id": 1508615151, "message_id": 7, "file": "path/to/photo.jpg", "caption": "check this"}
{"type": "voice", "from": "Hernán", "chat_id": 1508615151, "message_id": 8, "file": "path/to/voice.ogg", "transcription": "text"}
{"type": "command", "from": "Hernán", "chat_id": 1508615151, "command": "clear"}
```

### Outgoing (subagent writes to outbox.jsonl)

```json
{"type": "text", "chat_id": 1508615151, "text": "response here", "reply_to": 6}
{"type": "photo", "chat_id": 1508615151, "file": "path/to/image.png", "caption": "Here's what I generated"}
```

## Files

- **Bot script**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/bot.py`
- **Config**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/config.json`
- **Outbox**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox.jsonl`
- **Media inbox**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/media/inbox/`

## Sending a One-Off Message

If the user just wants to send a quick message without the full relay:

```python
# Write to outbox
{"type": "text", "chat_id": 1508615151, "text": "Your message here"}
```

Write this to `C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox.jsonl` (the bot must be running).
