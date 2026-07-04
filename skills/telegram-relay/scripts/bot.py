#!/usr/bin/env python3
"""
Fermi Telegram Relay Bot

Bridges Telegram to Antigravity via stdout/stdin JSON protocol.
- Incoming Telegram messages → JSON on stdout
- JSON on stdin → outgoing Telegram messages

Usage:
    python bot.py
"""

import asyncio
import json
import sys
import os
import logging
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

# Paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
MEDIA_DIR = None  # Set from config

# Logging — only to stderr so stdout stays clean for the protocol
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("fermi-relay")


def load_config() -> dict:
    """Load bot configuration."""
    if not CONFIG_PATH.exists():
        logger.error(f"Config not found: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def emit(msg: dict):
    """Write a JSON message to stdout for the agent to read."""
    line = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def is_allowed(user_id: int, allowed_ids: list[int]) -> bool:
    """Check if the user is allowed to interact with the bot."""
    if not allowed_ids:
        return True  # No restriction if list is empty
    return user_id in allowed_ids


# ---------------------------------------------------------------------------
# Telegram Handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context):
    """Handle /start command."""
    config = context.bot_data["config"]
    if not is_allowed(update.effective_user.id, config.get("allowed_user_ids", [])):
        return

    await update.message.reply_text(
        "👋 Hey! I'm Fermi, your Antigravity AI assistant.\n\n"
        "Send me a message and I'll process it with full agent capabilities.\n\n"
        "Commands:\n"
        "/clear — Start a fresh conversation\n"
        "/status — Check if the relay is connected"
    )

    # Also emit so the agent knows
    emit({
        "type": "command",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        "chat_id": update.effective_chat.id,
        "command": "start",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def cmd_clear(update: Update, context):
    """Handle /clear command — signals agent to reset conversation."""
    config = context.bot_data["config"]
    if not is_allowed(update.effective_user.id, config.get("allowed_user_ids", [])):
        return

    emit({
        "type": "command",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        "chat_id": update.effective_chat.id,
        "command": "clear",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    await update.message.reply_text("🔄 Conversation cleared. Fresh start!")


async def cmd_status(update: Update, context):
    """Handle /status command."""
    config = context.bot_data["config"]
    if not is_allowed(update.effective_user.id, config.get("allowed_user_ids", [])):
        return

    await update.message.reply_text("✅ Fermi relay is online and connected to Antigravity.")


async def handle_text(update: Update, context):
    """Handle incoming text messages."""
    config = context.bot_data["config"]
    if not is_allowed(update.effective_user.id, config.get("allowed_user_ids", [])):
        return

    emit({
        "type": "text",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        "chat_id": update.effective_chat.id,
        "message_id": update.message.message_id,
        "text": update.message.text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def handle_photo(update: Update, context):
    """Handle incoming photos — download and emit path."""
    config = context.bot_data["config"]
    if not is_allowed(update.effective_user.id, config.get("allowed_user_ids", [])):
        return

    # Get the highest resolution photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    # Download to media/inbox/
    inbox_dir = MEDIA_DIR / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    filename = f"photo_{update.message.message_id}_{photo.file_unique_id}.jpg"
    filepath = inbox_dir / filename
    await file.download_to_drive(str(filepath))

    emit({
        "type": "photo",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        "chat_id": update.effective_chat.id,
        "message_id": update.message.message_id,
        "file": str(filepath),
        "caption": update.message.caption or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def handle_voice(update: Update, context):
    """Handle incoming voice messages — download, transcribe if possible, emit."""
    config = context.bot_data["config"]
    if not is_allowed(update.effective_user.id, config.get("allowed_user_ids", [])):
        return

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    # Download to media/inbox/
    inbox_dir = MEDIA_DIR / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    filename = f"voice_{update.message.message_id}_{voice.file_unique_id}.ogg"
    filepath = inbox_dir / filename
    await file.download_to_drive(str(filepath))

    # Attempt transcription with Whisper
    transcription = ""
    try:
        import whisper
        model = whisper.load_model("small")
        result = model.transcribe(str(filepath))
        transcription = result.get("text", "")
        logger.info(f"Transcribed voice: {transcription[:100]}...")
    except ImportError:
        logger.warning("Whisper not installed — voice message sent without transcription")
    except Exception as e:
        logger.warning(f"Whisper transcription failed: {e}")

    emit({
        "type": "voice",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        "chat_id": update.effective_chat.id,
        "message_id": update.message.message_id,
        "file": str(filepath),
        "transcription": transcription,
        "duration": voice.duration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def handle_document(update: Update, context):
    """Handle incoming documents/files."""
    config = context.bot_data["config"]
    if not is_allowed(update.effective_user.id, config.get("allowed_user_ids", [])):
        return

    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)

    inbox_dir = MEDIA_DIR / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{update.message.message_id}_{doc.file_name or doc.file_unique_id}"
    filepath = inbox_dir / filename
    await file.download_to_drive(str(filepath))

    emit({
        "type": "document",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        "chat_id": update.effective_chat.id,
        "message_id": update.message.message_id,
        "file": str(filepath),
        "filename": doc.file_name or "",
        "mime_type": doc.mime_type or "",
        "caption": update.message.caption or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ---------------------------------------------------------------------------
# Outbox Poller — reads agent responses from file and sends to Telegram
# ---------------------------------------------------------------------------

OUTBOX_PATH = None  # Set from config/media_dir


def outbox_poller_thread(bot: Bot, loop: asyncio.AbstractEventLoop):
    """Poll outbox.jsonl for agent responses and send them to Telegram.

    The agent writes JSON lines to outbox.jsonl. This thread reads them,
    sends via Telegram, and clears the file.
    """
    while True:
        try:
            if OUTBOX_PATH and OUTBOX_PATH.exists() and OUTBOX_PATH.stat().st_size > 0:
                # Read and clear atomically
                with open(OUTBOX_PATH, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # Clear the file
                with open(OUTBOX_PATH, "w", encoding="utf-8") as f:
                    pass

                for raw_line in lines:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        chat_id = msg.get("chat_id")
                        if not chat_id:
                            logger.warning(f"No chat_id in outbox message: {line[:100]}")
                            continue
                        asyncio.run_coroutine_threadsafe(_send_response(bot, msg), loop)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in outbox: {e}")
        except Exception as e:
            logger.error(f"Outbox poller error: {e}")

        import time
        time.sleep(1)


async def _send_response(bot: Bot, msg: dict):
    """Send a response message to Telegram."""
    chat_id = msg.get("chat_id")
    msg_type = msg.get("type", "text")

    try:
        if msg_type == "text":
            text = msg.get("text", "")
            reply_to = msg.get("reply_to")
            max_len = 4096
            for i in range(0, len(text), max_len):
                chunk = text[i:i + max_len]
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=chunk,
                        reply_to_message_id=reply_to if i == 0 else None,
                        parse_mode="Markdown",
                    )
                except Exception:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=chunk,
                        reply_to_message_id=reply_to if i == 0 else None,
                    )

        elif msg_type == "photo":
            filepath = msg.get("file")
            caption = msg.get("caption", "")
            if filepath and Path(filepath).exists():
                with open(filepath, "rb") as f:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=f,
                        caption=caption or None,
                    )

        elif msg_type == "voice":
            filepath = msg.get("file")
            if filepath and Path(filepath).exists():
                with open(filepath, "rb") as f:
                    await bot.send_voice(chat_id=chat_id, voice=f)

        elif msg_type == "document":
            filepath = msg.get("file")
            caption = msg.get("caption", "")
            if filepath and Path(filepath).exists():
                with open(filepath, "rb") as f:
                    await bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        caption=caption or None,
                    )

        logger.info(f"Sent {msg_type} to chat {chat_id}")

    except Exception as e:
        logger.error(f"Error sending {msg_type} to Telegram: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import threading

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    config = load_config()
    token = config.get("bot_token", "")
    if not token or token == "REPLACE_WITH_YOUR_BOT_TOKEN":
        logger.error("Bot token not configured. Edit config.json with your bot token.")
        sys.exit(1)

    global MEDIA_DIR, OUTBOX_PATH
    MEDIA_DIR = Path(config.get("media_dir", SCRIPT_DIR / "media"))
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_PATH = MEDIA_DIR / "outbox.jsonl"

    # Build the application
    app = Application.builder().token(token).build()
    app.bot_data["config"] = config

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Fermi Telegram relay starting...")
    logger.info(f"Outbox path: {OUTBOX_PATH}")
    emit({"type": "system", "event": "bot_started", "timestamp": datetime.now(timezone.utc).isoformat()})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        async with app:
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)

            # Start outbox poller in a daemon thread
            poller_thread = threading.Thread(
                target=outbox_poller_thread,
                args=(app.bot, loop),
                daemon=True,
            )
            poller_thread.start()

            logger.info("Fermi relay is online. Waiting for messages...")
            try:
                await asyncio.Event().wait()
            finally:
                await app.updater.stop()
                await app.stop()

    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        loop.close()


if __name__ == "__main__":
    main()

