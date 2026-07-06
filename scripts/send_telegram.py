#!/usr/bin/env python3
import asyncio
import argparse
from pathlib import Path
from telegram import Bot

def load_token() -> str:
    import os
    token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN")
    if token:
        return token
    
    # Try .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() in ("TELEGRAM_TOKEN", "BOT_TOKEN"):
                            return v.strip().strip("'\"")
        except Exception:
            pass
            
    # Try config.json
    config_path = Path(__file__).parent.parent / "skills" / "telegram-relay" / "scripts" / "config.json"
    if config_path.exists():
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("bot_token")
        except Exception:
            pass
            
    return ""

async def main():
    parser = argparse.ArgumentParser(description="Send messages directly to Telegram")
    parser.add_argument("--chat-id", type=int, default=1508615151, help="Telegram chat ID")
    parser.add_argument("--text", type=str, help="Text message to send")
    parser.add_argument("--voice", type=str, help="Path to voice ogg file to send")
    parser.add_argument("--reply-to", type=int, help="Message ID to reply to")
    args = parser.parse_args()

    token = load_token()
    bot = Bot(token=token)

    if args.voice:
        voice_path = Path(args.voice)
        if not voice_path.exists():
            print(f"ERROR: Voice file not found: {voice_path}")
            return
        print(f"Sending voice message from {voice_path}...")
        try:
            with open(voice_path, "rb") as f:
                await bot.send_voice(
                    chat_id=args.chat_id,
                    voice=f,
                    reply_to_message_id=args.reply_to
                )
            print("Voice message sent successfully!")
        except Exception as e:
            print(f"Failed to send voice message: {e}")

    if args.text:
        print(f"Sending text message...")
        try:
            await bot.send_message(
                chat_id=args.chat_id,
                text=args.text,
                reply_to_message_id=args.reply_to if not args.voice else None,
                parse_mode="Markdown"
            )
            print("Text message sent successfully!")
        except Exception as e:
            # Fallback if markdown parsing fails
            try:
                await bot.send_message(
                    chat_id=args.chat_id,
                    text=args.text,
                    reply_to_message_id=args.reply_to if not args.voice else None
                )
                print("Text message sent successfully (fallback plain text)!")
            except Exception as ex:
                print(f"Failed to send text message: {ex}")

if __name__ == "__main__":
    asyncio.run(main())
