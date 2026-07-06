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
import base64
import json
import sys
import os
import time
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    MessageReactionHandler,
    filters,
)

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    FastAPI = None
    WebSocket = None
    WebSocketDisconnect = None
    Request = None
    StaticFiles = None
    uvicorn = None

try:
    import google.genai as genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

# Paths
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
MEDIA_DIR = None  # Set from config
INBOX_PATH = None  # Set from config/media_dir
TELEGRAM_LOG_DIR = Path("D:/dev/Fermi/memory/telegram")
LOCKFILE = Path(r"C:\Users\hernan.g\.gemini\config\plugins\fermi\media\bot.pid")

# Live Call globals
ACTIVE_SESSIONS = []
MODEL = "gemini-3.1-flash-live-preview"
MEMORY_DIR_PLUGIN = Path(r"C:\Users\hernan.g\.gemini\config\plugins\fermi\memory")
MEMORY_DIR_WORKSPACE = Path(r"D:\dev\Fermi\memory")
VOICE = "Puck"
fastapi_app = FastAPI() if FastAPI else None

def build_system_instruction() -> str:
    instruction = "You are Fermi, Hernán's AI assistant. You are currently in a real-time LIVE VOICE conversation through a phone call.\n\n"
    
    # Load plugin memory
    for filename in ["USER.md", "MEMORY.md"]:
        filepath = MEMORY_DIR_PLUGIN / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                instruction += f"\n--- {filename} ---\n{f.read()}\n"
                
    # Load workspace memory
    for filename in ["BELIEFS.md", "TODAY.md"]:
        filepath = MEMORY_DIR_WORKSPACE / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                instruction += f"\n--- {filename} ---\n{f.read()}\n"
                
    # Load today's Telegram log for recent context
    today_str = datetime.now().strftime("%Y-%m-%d")
    telegram_log_path = MEMORY_DIR_WORKSPACE / "telegram" / f"telegram_{today_str}.jsonl"
    if telegram_log_path.exists():
        instruction += f"\n--- RECENT MESSAGES (TELEGRAM) ---\n"
        with open(telegram_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-20:]:
                try:
                    data = json.loads(line)
                    sender = data.get("from", "Fermi") if data.get("from") else "Fermi"
                    text = data.get("text", "")
                    if text:
                        instruction += f"{sender}: {text}\n"
                except:
                    pass
                
    instruction += """
You have native access to tools. For 90% of casual chatting, answer natively using your context. 
However, if Hernán asks you to run a command, check his codebase, search the internet, or do something complex that requires deep capabilities, you MUST use the `ask_antigravity` tool.

CRITICAL INSTRUCTION FOR ask_antigravity: 
Before calling the `ask_antigravity` tool, you MUST first say something out loud to let him know you are thinking, for example: "Give me a second to check that", or "Let me ask my core systems". Do NOT stay silent before calling the tool.

If Hernán asks you to remember a simple fact for the future, use the `update_memory` tool.
Keep your responses conversational, natural, and brief.
"""
    return instruction


async def process_antigravity_query(client, session, query: str, call_id: str):
    request_data = {
        "type": "live_request",
        "call_id": call_id,
        "query": query
    }
    # The "> " suffix tricks the Antigravity task manager into thinking this is a prompt, waking up the agent.
    print(f"\nAntigravity, please process this live_request:\n{json.dumps(request_data)}\n> ", end="", flush=True)
    
    try:
        await session.send_tool_response(
            function_responses=[{
                "id": call_id,
                "name": "ask_antigravity",
                "response": {"result": "Petición enviada a Antigravity. Se procesará asíncronamente en segundo plano. Avisaré a Hernán cuando tenga respuesta."}
            }]
        )
    except Exception as e:
        logger.error(f"[Core] Error sending tool response: {e}")


if fastapi_app:
    @fastapi_app.post("/inject")
    async def inject_message(request: Request):
        data = await request.json()
        message = data.get("message", "")
        if not message:
            return {"status": "error", "message": "Missing 'message' field"}
            
        logger.info(f"[Core -> Live Inject]: {message}")
        
        count = 0
        for session in ACTIVE_SESSIONS:
            try:
                await session.send_client_content(
                    turns=[
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=f"Antigravity reporta los resultados de la consulta: {message}")]
                        )
                    ],
                    turn_complete=True
                )
                count += 1
            except Exception as e:
                logger.error(f"[Core] Error injecting to session: {e}")
                
        return {"status": "success", "sessions_notified": count}


    @fastapi_app.websocket("/ws/call")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        if not genai:
            await websocket.send_text("Error: google-genai is not installed.")
            await websocket.close()
            return
            
        config = load_config()
        api_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            await websocket.send_text("Error: gemini_api_key not found in config or environment.")
            await websocket.close()
            return

        client = genai.Client(api_key=api_key)
        
        ask_antigravity_tool = types.FunctionDeclaration(
            name="ask_antigravity",
            description="Query the main Antigravity agent to run codebase commands, perform web searches, or retrieve complex deep context. Use this whenever you can't fulfill the request natively.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(type="STRING", description="A detailed instruction or question for Antigravity to process.")
                },
                required=["query"]
            )
        )
        
        update_memory_tool = types.FunctionDeclaration(
            name="update_memory",
            description="Save a persistent fact about the user or the world to MEMORY.md for future sessions.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "fact": types.Schema(type="STRING", description="The fact to remember.")
                },
                required=["fact"]
            )
        )

        tools = [types.Tool(function_declarations=[ask_antigravity_tool, update_memory_tool])]

        live_config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=VOICE
                    )
                )
            ),
            system_instruction=types.Content(parts=[types.Part.from_text(text=build_system_instruction())]),
            tools=tools
        )
        
        try:
            async with client.aio.live.connect(model=MODEL, config=live_config) as session:
                logger.info("[Server] Connected to Gemini Live API Natively")
                ACTIVE_SESSIONS.append(session)
                try:
                    async def receive_from_frontend():
                        try:
                            while True:
                                data = await websocket.receive_bytes()
                                await session.send_realtime_input(audio={"data": data, "mime_type": "audio/pcm"})
                        except WebSocketDisconnect:
                            logger.info("[Server] Client disconnected.")
                        except Exception as e:
                            logger.error(f"[Server] Error receiving from frontend: {e}")

                    async def send_to_frontend():
                        try:
                            while True:
                                async for response in session.receive():
                                    if response.server_content is not None:
                                        model_turn = response.server_content.model_turn
                                        if model_turn is not None:
                                            for part in model_turn.parts:
                                                if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                                                    await websocket.send_bytes(part.inline_data.data)
                                                    
                                    if response.tool_call is not None:
                                        for function_call in response.tool_call.function_calls:
                                            if function_call.name == "ask_antigravity":
                                                query = function_call.args.get("query", "")
                                                logger.info(f"[Live] Asking core: {query}")
                                                asyncio.create_task(process_antigravity_query(client, session, query, function_call.id))
                                                
                                            elif function_call.name == "update_memory":
                                                fact = function_call.args.get("fact", "")
                                                logger.info(f"[Live] Remembering: {fact}")
                                                
                                                # Append directly to MEMORY.md
                                                memory_file = MEMORY_DIR_PLUGIN / "MEMORY.md"
                                                if memory_file.exists():
                                                    with open(memory_file, "a", encoding="utf-8") as f:
                                                        f.write(f"\n- [LIVE VOICE]: {fact}")
                                                
                                                await session.send_tool_response(
                                                    function_responses=[{
                                                        "id": function_call.id,
                                                        "name": "update_memory",
                                                        "response": {"result": "Fact successfully saved to memory."}
                                                    }]
                                                )
                                asyncio.sleep(0.01)
                        except Exception as e:
                            logger.error(f"[Server] Error sending to frontend: {e}")

                    await asyncio.gather(
                        receive_from_frontend(),
                        send_to_frontend()
                    )
                finally:
                    if session in ACTIVE_SESSIONS:
                        ACTIVE_SESSIONS.remove(session)
        except Exception as e:
            logger.error(f"[Server] Gemini Connection Error: {e}")
            await websocket.close()

    # Mount live app static files if the directory exists
    live_app_path = r"D:\dev\Fermi\scripts\live_app"
    if os.path.exists(live_app_path):
        fastapi_app.mount("/app", StaticFiles(directory=live_app_path, html=True), name="static")




def acquire_lock():
    """Ensure only one bot instance runs. Kill any existing instance first."""
    if LOCKFILE.exists():
        try:
            old_pid = int(LOCKFILE.read_text().strip())
            # Check if the old process is still alive
            import psutil
            if psutil.pid_exists(old_pid):
                proc = psutil.Process(old_pid)
                if "python" in proc.name().lower():
                    logger.warning(f"Killing existing bot instance (PID {old_pid})")
                    proc.terminate()
                    proc.wait(timeout=5)
        except (ValueError, ImportError, Exception) as e:
            logger.warning(f"Could not check/kill old process: {e}")
            # Fallback: try taskkill
            try:
                old_pid = int(LOCKFILE.read_text().strip())
                import subprocess
                subprocess.run(["taskkill", "/F", "/PID", str(old_pid)],
                             capture_output=True, timeout=5)
            except Exception:
                pass
    # Write our PID
    LOCKFILE.parent.mkdir(parents=True, exist_ok=True)
    LOCKFILE.write_text(str(os.getpid()))
    logger.info(f"Lock acquired (PID {os.getpid()})")

# Conversation context buffer for transcription
MESSAGE_HISTORY: deque = deque(maxlen=20)

# Active typing tasks to show typing indicator while agent processes
ACTIVE_TYPING_TASKS = {}


def start_typing_indicator(bot: Bot, chat_id: int):
    """Start a background loop to show typing action on Telegram."""
    if chat_id in ACTIVE_TYPING_TASKS:
        try:
            ACTIVE_TYPING_TASKS[chat_id].cancel()
        except Exception:
            pass

    async def _indicator_loop():
        try:
            # Loop for max 60 seconds (15 * 4)
            for _ in range(15):
                try:
                    await bot.send_chat_action(chat_id=chat_id, action="typing")
                except Exception:
                    pass
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass
        finally:
            ACTIVE_TYPING_TASKS.pop(chat_id, None)

    ACTIVE_TYPING_TASKS[chat_id] = asyncio.create_task(_indicator_loop())


# Gemini client for voice transcription
GEMINI_CLIENT = None

# Logging — only to stderr so stdout stays clean for the protocol
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("fermi-relay")


def load_env() -> dict:
    """Load variables from D:/dev/Fermi/.env if it exists."""
    env_vars = {}
    env_path = Path("D:/dev/Fermi/.env")
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip("'\"")
        except Exception as e:
            logger.warning(f"Failed to load .env: {e}")
    return env_vars


def load_config() -> dict:
    """Load bot configuration."""
    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to parse config.json: {e}")
            
    # Load env vars
    env = load_env()
    
    # Overlay keys
    config["bot_token"] = env.get("TELEGRAM_TOKEN") or env.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN") or config.get("bot_token")
    config["gemini_api_key"] = env.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") or config.get("gemini_api_key")
    config["call_url"] = env.get("CALL_URL") or os.environ.get("CALL_URL") or config.get("call_url")
    config["media_dir"] = env.get("MEDIA_DIR") or os.environ.get("MEDIA_DIR") or config.get("media_dir")
    config["outbox_path"] = env.get("OUTBOX_PATH") or os.environ.get("OUTBOX_PATH") or config.get("outbox_path")
    return config


def log_message(msg: dict, direction: str = "in"):
    """Append a message to the daily conversation log.
    
    Files: D:/dev/Fermi/memory/telegram/telegram_YYYY-MM-DD.jsonl
    Each line: {"direction": "in"|"out", "timestamp": ..., ...original msg...}
    Files are archived indefinitely — never deleted.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        TELEGRAM_LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = TELEGRAM_LOG_DIR / f"telegram_{today}.jsonl"
        entry = {"direction": direction, **msg}
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write conversation log: {e}")


def emit(msg: dict):
    """Write a JSON message to stdout and inbox.jsonl for the agent to read."""
    line = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

    # Log incoming message to daily conversation log
    if msg.get("type") not in ("system",):
        log_message(msg, direction="in")

    # Also append to inbox.jsonl for the file watcher
    if INBOX_PATH:
        try:
            with open(INBOX_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            logger.warning(f"Failed to write to inbox: {e}")


def is_chat_allowed(update: Update, config: dict) -> bool:
    """Check if this message should be processed based on chat context.
    
    - Private chats: check against allowed_user_ids
    - Group chats: check against allowed_group_ids
    """
    chat = update.effective_chat
    chat_type = chat.type if chat else "private"
    
    if chat_type == "private":
        allowed_users = config.get("allowed_user_ids", [])
        if not allowed_users:
            return True
        return update.effective_user.id in allowed_users
    else:
        # Group or supergroup
        allowed_groups = config.get("allowed_group_ids", [])
        if not allowed_groups:
            return False  # Don't allow unknown groups by default
        return chat.id in allowed_groups


def chat_info(update: Update) -> dict:
    """Extract chat context fields for emitted JSON."""
    chat = update.effective_chat
    info = {
        "chat_id": chat.id,
        "chat_type": chat.type,  # private, group, supergroup
    }
    if chat.type != "private":
        info["chat_title"] = chat.title or ""
    return info


# ---------------------------------------------------------------------------
# Voice Transcription via Gemini Flash
# ---------------------------------------------------------------------------

async def transcribe_voice(filepath: Path) -> str:
    """Transcribe a voice message using Gemini 2.5 Flash with conversation context."""
    if not GEMINI_CLIENT:
        logger.warning("Gemini client not configured — skipping transcription")
        return ""

    try:
        audio_bytes = filepath.read_bytes()
        audio_b64 = base64.b64encode(audio_bytes).decode()

        # Build context prompt from recent messages
        context_lines = list(MESSAGE_HISTORY)
        context_block = ""
        if context_lines:
            context_block = (
                "Here is the recent conversation for context "
                "(use it to understand proper names, topics, and intent — "
                "do NOT include any of this in the transcription):\n\n"
                + "\n".join(context_lines)
                + "\n\n"
            )

        prompt = (
            f"{context_block}"
            "Transcribe this voice message exactly as spoken. "
            "Output ONLY the transcription, nothing else. "
            "Do not add quotes, labels, or commentary."
        )

        response = GEMINI_CLIENT.models.generate_content(
            model="gemini-3.5-flash",
            contents=[{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": "audio/ogg", "data": audio_b64}},
                    {"text": prompt},
                ],
            }],
        )

        transcription = response.text.strip()
        logger.info(f"Transcribed voice: {transcription[:100]}...")
        return transcription

    except Exception as e:
        logger.error(f"Gemini transcription failed: {e}")
        return ""


# ---------------------------------------------------------------------------
# Telegram Handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context):
    """Handle /start command."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
        return

    # Update menu button for this chat explicitly
    url = config.get("call_url")
    if url:
        try:
            await context.bot.set_chat_menu_button(
                chat_id=update.effective_chat.id,
                menu_button=MenuButtonWebApp(
                    text="📞 Call Fermi",
                    web_app=WebAppInfo(url=url)
                )
            )
        except Exception as e:
            logger.error(f"Failed to set chat menu button in /start: {e}")

    await update.message.reply_text(
        "👋 Hey! I'm Fermi, your Antigravity AI assistant.\n\n"
        "Send me a message and I'll process it with full agent capabilities.\n\n"
        "Commands:\n"
        "/clear — Start a fresh conversation\n"
        "/status — Check if the relay is connected\n"
        "/call — Start a Live Voice Call"
    )

    # Also emit so the agent knows
    emit({
        "type": "command",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        **chat_info(update),
        "command": "start",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def cmd_clear(update: Update, context):
    """Handle /clear command — signals agent to reset conversation."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
        return

    emit({
        "type": "command",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        **chat_info(update),
        "command": "clear",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    await update.message.reply_text("🔄 Conversation cleared. Fresh start!")


async def cmd_status(update: Update, context):
    """Handle /status command."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
        return

    await update.message.reply_text("✅ Fermi relay is online and connected to Antigravity.")


async def cmd_call(update: Update, context):
    """Handle /call command — send Web App button."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
        return

    url = config.get("call_url")
    if not url:
        await update.message.reply_text("Call URL not set! Use /setcallurl <https://...>")
        return

    # Update menu button for this chat explicitly
    try:
        await context.bot.set_chat_menu_button(
            chat_id=update.effective_chat.id,
            menu_button=MenuButtonWebApp(
                text="📞 Call Fermi",
                web_app=WebAppInfo(url=url)
            )
        )
    except Exception as e:
        logger.error(f"Failed to set chat menu button in /call: {e}")

    keyboard = [[InlineKeyboardButton("📞 Call Fermi", web_app=WebAppInfo(url=url))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Tap below to start a live voice call:", reply_markup=reply_markup)


async def cmd_setcallurl(update: Update, context):
    """Handle /setcallurl command."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
        return

    if not context.args:
        await update.message.reply_text("Usage: /setcallurl https://...\n(Example: /setcallurl https://fermi.loca.lt)")
        return

    url = context.args[0]
    config["call_url"] = url
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        
        # Dynamically set the menu button to the new call page
        await context.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📞 Call Fermi",
                web_app=WebAppInfo(url=url)
            )
        )
        await update.message.reply_text(f"✅ Call URL set to:\n{url}\nMenu button updated to 📞 Call Fermi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to save config or update menu button: {e}")


async def handle_text(update: Update, context):
    """Handle incoming text messages."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
        return

    text = update.message.text
    # Track in conversation history for transcription context
    MESSAGE_HISTORY.append(f"{update.effective_user.first_name}: {text}")

    emit({
        "type": "text",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        **chat_info(update),
        "message_id": update.message.message_id,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    start_typing_indicator(context.bot, update.effective_chat.id)


async def handle_photo(update: Update, context):
    """Handle incoming photos — download and emit path."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
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
        **chat_info(update),
        "message_id": update.message.message_id,
        "file": str(filepath),
        "caption": update.message.caption or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    start_typing_indicator(context.bot, update.effective_chat.id)


async def handle_voice(update: Update, context):
    """Handle incoming voice messages — download, transcribe via Gemini Flash, emit."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
        return

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    # Download to media/inbox/
    inbox_dir = MEDIA_DIR / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    filename = f"voice_{update.message.message_id}_{voice.file_unique_id}.ogg"
    filepath = inbox_dir / filename
    await file.download_to_drive(str(filepath))

    # Transcribe with Gemini Flash + conversation context
    transcription = await transcribe_voice(filepath)

    # Track in conversation history
    if transcription:
        MESSAGE_HISTORY.append(f"{update.effective_user.first_name}: {transcription}")

    emit({
        "type": "voice",
        "from": update.effective_user.first_name,
        "user_id": update.effective_user.id,
        **chat_info(update),
        "message_id": update.message.message_id,
        "file": str(filepath),
        "transcription": transcription,
        "duration": voice.duration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    start_typing_indicator(context.bot, update.effective_chat.id)


async def handle_document(update: Update, context):
    """Handle incoming documents/files."""
    config = context.bot_data["config"]
    if not is_chat_allowed(update, config):
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
        **chat_info(update),
        "message_id": update.message.message_id,
        "file": str(filepath),
        "filename": doc.file_name or "",
        "mime_type": doc.mime_type or "",
        "caption": update.message.caption or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    start_typing_indicator(context.bot, update.effective_chat.id)


async def handle_reaction(update: Update, context):
    """Handle message reactions (emoji responses)."""
    config = context.bot_data["config"]
    reaction = update.message_reaction
    if not reaction:
        return

    # For reactions, check group permission by chat ID
    chat = reaction.chat
    chat_type = chat.type if chat else "private"
    if chat_type == "private":
        user = reaction.user
        allowed_users = config.get("allowed_user_ids", [])
        if user and allowed_users and user.id not in allowed_users:
            return
    else:
        allowed_groups = config.get("allowed_group_ids", [])
        if allowed_groups and chat.id not in allowed_groups:
            return

    user = reaction.user

    # Get new reactions (just added)
    new_emojis = []
    for r in (reaction.new_reaction or []):
        if hasattr(r, 'emoji'):
            new_emojis.append(r.emoji)
        elif hasattr(r, 'custom_emoji_id'):
            new_emojis.append(f"custom:{r.custom_emoji_id}")

    old_emojis = []
    for r in (reaction.old_reaction or []):
        if hasattr(r, 'emoji'):
            old_emojis.append(r.emoji)
        elif hasattr(r, 'custom_emoji_id'):
            old_emojis.append(f"custom:{r.custom_emoji_id}")

    reaction_msg = {
        "type": "reaction",
        "from": user.first_name if user else "unknown",
        "user_id": user.id if user else 0,
        "chat_id": chat.id,
        "chat_type": chat_type,
        "message_id": reaction.message_id,
        "new_reactions": new_emojis,
        "old_reactions": old_emojis,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if chat_type != "private":
        reaction_msg["chat_title"] = chat.title or ""
    emit(reaction_msg)


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
                        # Process sequentially — wait for each message to send
                        # before starting the next (preserves ordering)
                        future = asyncio.run_coroutine_threadsafe(_send_response(bot, msg), loop)
                        future.result(timeout=120)  # Wait up to 2min (TTS can be slow)
                        time.sleep(0.5)  # Small gap between messages
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in outbox: {e}")
                    except Exception as e:
                        logger.error(f"Error processing outbox message: {e}")
        except Exception as e:
            logger.error(f"Outbox poller error: {e}")

        time.sleep(1)


async def _send_response(bot: Bot, msg: dict):
    """Send a response message to Telegram."""
    chat_id = msg.get("chat_id")
    msg_type = msg.get("type", "text")

    # Cancel any active typing indicator
    if chat_id in ACTIVE_TYPING_TASKS:
        try:
            ACTIVE_TYPING_TASKS[chat_id].cancel()
        except Exception:
            pass

    try:
        # Send appropriate indicator BEFORE any processing
        try:
            action = "record_voice" if msg_type == "voice" else "typing"
            await bot.send_chat_action(chat_id=chat_id, action=action)
        except Exception:
            pass  # Non-critical

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
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=60,
                    )


        elif msg_type == "voice":
            filepath = msg.get("file")
            text = msg.get("text", "")
            # If no file but has text, generate via TTS
            if not filepath and text:
                logger.info(f"Generating TTS for: {text[:80]}...")
                try:
                    # Use the fermi-tts script
                    tts_path = "C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/fermi-tts/scripts/tts.py"
                    cmd = [sys.executable, tts_path, "--text", text]
                    if msg.get("voice"):
                        cmd.extend(["--voice", msg.get("voice")])
                    cmd.append("--humanize")
                    
                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: __import__("subprocess").run(
                            cmd,
                            capture_output=True, text=True, timeout=180,
                        )
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        filepath = result.stdout.strip().splitlines()[-1].strip()
                        logger.info(f"TTS generated: {filepath}")
                    else:
                        logger.error(f"TTS failed (rc={result.returncode}): {result.stderr[:200]}")
                except Exception as e:
                    logger.error(f"TTS error: {e}")

            # Now send the file
            if not filepath:
                logger.warning("Voice message has no 'file' field and TTS failed")
            elif not Path(filepath).exists():
                logger.warning(f"Voice file not found: {filepath}")
            else:
                file_size = Path(filepath).stat().st_size
                logger.info(f"Sending voice file: {filepath} ({file_size} bytes)")
                if file_size == 0:
                    logger.warning(f"Voice file is empty: {filepath}")
                else:
                    with open(filepath, "rb") as f:
                        await bot.send_voice(
                            chat_id=chat_id,
                            voice=f,
                            read_timeout=60,
                            write_timeout=60,
                            connect_timeout=60,
                        )

        elif msg_type == "document":
            filepath = msg.get("file")
            caption = msg.get("caption", "")
            if filepath and Path(filepath).exists():
                with open(filepath, "rb") as f:
                    await bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        caption=caption or None,
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=60,
                    )


        elif msg_type == "reaction":
            from telegram import ReactionTypeEmoji
            message_id = msg.get("message_id")
            emoji = msg.get("emoji", "👍")
            is_big = msg.get("is_big", False)
            if message_id:
                await bot.set_message_reaction(
                    chat_id=chat_id,
                    message_id=message_id,
                    reaction=[ReactionTypeEmoji(emoji=emoji)],
                    is_big=is_big,
                )

        logger.info(f"Sent {msg_type} to chat {chat_id}")

        # Log outgoing message to daily conversation log
        log_message(msg, direction="out")

        # Track bot responses in conversation history for transcription context
        if msg_type == "text":
            bot_text = msg.get("text", "")
            if bot_text:
                MESSAGE_HISTORY.append(f"Fermi: {bot_text[:200]}")

    except Exception as e:
        logger.error(f"Error sending {msg_type} to Telegram: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import threading

    # Ensure only one bot instance runs at a time
    acquire_lock()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    config = load_config()
    token = config.get("bot_token", "")
    if not token or token == "REPLACE_WITH_YOUR_BOT_TOKEN":
        logger.error("Bot token not configured. Edit config.json with your bot token.")
        sys.exit(1)

    global MEDIA_DIR, OUTBOX_PATH, INBOX_PATH, GEMINI_CLIENT
    MEDIA_DIR = Path(config.get("media_dir", SCRIPT_DIR / "media"))
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_PATH = MEDIA_DIR / "outbox.jsonl"
    INBOX_PATH = MEDIA_DIR / "inbox.jsonl"

    # Initialize Gemini client for voice transcription
    gemini_key = config.get("gemini_api_key", "")
    if gemini_key:
        try:
            import google.genai as genai
            GEMINI_CLIENT = genai.Client(api_key=gemini_key)
            logger.info("Gemini client initialized for voice transcription")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
    else:
        logger.warning("No gemini_api_key in config — voice transcription disabled")

    # Build the application
    app = Application.builder().token(token).build()
    app.bot_data["config"] = config

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("call", cmd_call))
    app.add_handler(CommandHandler("setcallurl", cmd_setcallurl))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageReactionHandler(handle_reaction))

    logger.info("Fermi Telegram relay starting...")
    logger.info(f"Outbox path: {OUTBOX_PATH}")
    emit({"type": "system", "event": "bot_started", "timestamp": datetime.now(timezone.utc).isoformat()})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        async with app:
            await app.start()

            # Set the menu button if call_url is configured on startup
            url = config.get("call_url")
            if url:
                try:
                    await app.bot.set_chat_menu_button(
                        menu_button=MenuButtonWebApp(
                            text="📞 Call Fermi",
                            web_app=WebAppInfo(url=url)
                        )
                    )
                    logger.info(f"Chat menu button set to call URL: {url}")
                except Exception as e:
                    logger.error(f"Failed to set menu button on startup: {e}")
            await app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=[
                    "message", "edited_message", "channel_post",
                    "message_reaction", "callback_query",
                ],
            )

            # Start outbox poller in a daemon thread
            poller_thread = threading.Thread(
                target=outbox_poller_thread,
                args=(app.bot, loop),
                daemon=True,
            )
            poller_thread.start()

            # Start Uvicorn Server in the same loop
            if fastapi_app and uvicorn:
                uvicorn_config = uvicorn.Config(
                    fastapi_app,
                    host="0.0.0.0",
                    port=8000,
                    log_level="warning"
                )
                uvicorn_server = uvicorn.Server(uvicorn_config)
                
                logger.info("Fermi unified gateway starting FastAPI on port 8000 & Telegram Relay...")
                try:
                    await asyncio.gather(
                        uvicorn_server.serve(),
                        asyncio.Event().wait()
                    )
                finally:
                    await app.updater.stop()
                    await app.stop()
            else:
                logger.info("Fermi relay is online (FastAPI/Live Call disabled). Waiting for messages...")
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

