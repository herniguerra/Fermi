#!/usr/bin/env python3
import os
import sys
import json
import re
import argparse
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Try to import google-genai
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Warning: google-genai package not found. Please install it.", file=sys.stderr)

# Configuration & Paths
FERMI_DIR = Path("D:/dev/Fermi")
MEMORY_DIR = FERMI_DIR / "memory"
REFLECTIONS_DIR = MEMORY_DIR / "reflections"
DREAMS_DIR = MEMORY_DIR / "dreams"
TODAY_ARCHIVE_DIR = MEMORY_DIR / "today"
BELIEFS_PATH = MEMORY_DIR / "BELIEFS.md"
MEMORY_PATH = MEMORY_DIR / "MEMORY.md"
USER_PATH = MEMORY_DIR / "USER.md"
TODAY_PATH = MEMORY_DIR / "TODAY.md"
TELEGRAM_LOG_DIR = MEMORY_DIR / "telegram"
OUTBOX_PATH = Path("C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox.jsonl")

def get_api_key():
    """Retrieve Gemini API key from environment, config files, or .env."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
        
    config_path = Path("C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/config.json")
    if config_path.exists():
        try:
            with open(config_path) as f:
                data = json.load(f)
                key = data.get("gemini_api_key")
                if key:
                    return key
        except Exception:
            pass
            
    dotenv_path = Path("c:/Users/hernan.g/Desktop/NDN/.env")
    if dotenv_path.exists():
        try:
            with open(dotenv_path) as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=")[1].strip()
        except Exception:
            pass
            
    return None

def extract_tag_content(text, tag):
    """Robustly extract content enclosed in XML-style tags."""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def get_recent_transcripts(hours=24):
    """Scan Antigravity brain directory for transcript logs from the last 24h."""
    brain_dir = Path(r"C:\Users\hernan.g\.gemini\antigravity\brain")
    if not brain_dir.exists():
        return "No local conversation logs found."
        
    cutoff = datetime.now() - timedelta(hours=hours)
    transcript_texts = []
    
    for p in brain_dir.iterdir():
        if not p.is_dir():
            continue
            
        log_dir = p / ".system_generated" / "logs"
        transcript_file = log_dir / "transcript.jsonl"
        if not transcript_file.exists():
            transcript_file = p / "transcript.jsonl"
            
        if not transcript_file.exists():
            continue
            
        mtime = datetime.fromtimestamp(transcript_file.stat().st_mtime)
        if mtime < cutoff:
            continue
            
        try:
            content = []
            with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        source = data.get("source")
                        step_type = data.get("type")
                        step_content = data.get("content")
                        
                        if step_type == "USER_INPUT" and step_content:
                            content.append(f"User: {step_content.strip()}")
                        elif step_type in ("PLANNER_RESPONSE", "MODEL") and step_content:
                            content.append(f"Fermi: {step_content.strip()}")
                    except Exception:
                        pass
            if content:
                transcript_texts.append(
                    f"--- Conversation {p.name} (last modified {mtime.strftime('%Y-%m-%d %H:%M')}) ---\n" +
                    "\n".join(content)
                )
        except Exception as e:
            print(f"Error reading transcript {transcript_file}: {e}", file=sys.stderr)
            
    if transcript_texts:
        return "\n\n".join(transcript_texts)
    return "No conversation transcripts in the last 24 hours."

def get_recent_telegram_messages(hours=24):
    """Read Telegram messages logged in the last 24h."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    telegram_texts = []
    
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    dates = [yesterday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")]
    
    for date_str in dates:
        log_path = TELEGRAM_LOG_DIR / f"telegram_{date_str}.jsonl"
        if not log_path.exists():
            continue
            
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        ts_str = data.get("timestamp")
                        if not ts_str:
                            continue
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts < cutoff:
                            continue
                            
                        sender_name = data.get("from", {}).get("first_name", "User")
                        text = data.get("text", "")
                        if not text and data.get("caption"):
                            text = data.get("caption")
                        if not text and data.get("voice"):
                            text = f"[Voice Message: {data.get('transcription', 'no transcription')}]"
                            
                        direction = data.get("direction", "in")
                        if direction == "in":
                            telegram_texts.append(f"[{ts.strftime('%H:%M')}] {sender_name}: {text}")
                        else:
                            out_text = data.get("text", "")
                            telegram_texts.append(f"[{ts.strftime('%H:%M')}] Fermi (to {sender_name}): {out_text}")
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error reading telegram log {log_path}: {e}", file=sys.stderr)
            
    if telegram_texts:
        return "--- Telegram Activity ---\n" + "\n".join(telegram_texts)
    return "No Telegram activity in the last 24 hours."

def fetch_rss_feed(url, max_items=5):
    """Fetch and parse titles from an RSS feed using standard libraries."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = []
            for item in root.findall(".//item")[:max_items]:
                title = item.find("title")
                title_text = title.text if title is not None else ""
                link = item.find("link")
                link_text = link.text if link is not None else ""
                items.append(f"- {title_text.strip()} ({link_text.strip()})")
            return "\n".join(items)
    except Exception as e:
        return f"Error fetching RSS from {url}: {e}"

def get_buenos_aires_weather():
    """Fetch current and daily forecast for Buenos Aires from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=-34.61315&longitude=-58.37723&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=America/Argentina/Buenos_Aires&forecast_days=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            temp = current.get("temperature_2m")
            app_temp = current.get("apparent_temperature")
            humidity = current.get("relative_humidity_2m")
            wind = current.get("wind_speed_10m")
            rain = current.get("rain")
            
            temp_max = daily.get("temperature_2m_max", [temp])[0]
            temp_min = daily.get("temperature_2m_min", [temp])[0]
            
            wmo_code = current.get("weather_code", 0)
            wmo_desc = {
                0: "Despejado", 1: "Principalmente despejado", 2: "Parcialmente nublado", 3: "Nublado",
                45: "Niebla", 48: "Niebla ralo", 51: "Llovizna ligera", 53: "Llovizna moderada", 55: "Llovizna densa",
                61: "Lluvia ligera", 63: "Lluvia moderada", 65: "Lluvia fuerte", 71: "Nieve ligera", 73: "Nieve moderada",
                75: "Nieve fuerte", 80: "Lluvias ligeras", 81: "Lluvias moderadas", 82: "Lluvias violentas",
                95: "Tormenta eléctrica", 96: "Tormenta con granizo ligero", 97: "Tormenta con granizo fuerte"
            }
            desc = wmo_desc.get(wmo_code, "Condiciones variables")
            
            weather_str = f"Temperatura: {temp_min}°C – {temp_max}°C (actual {temp}°C)\n"
            weather_str += f"Sensación térmica: {app_temp}°C\n"
            weather_str += f"Condición: {desc}\n"
            weather_str += f"Viento: {wind} km/h\n"
            weather_str += f"Humedad: {humidity}%"
            if rain and rain > 0:
                weather_str += f"\nPrecipitación: {rain} mm"
            return weather_str
    except Exception as e:
        return f"Error al obtener el clima de Buenos Aires: {e}"

def action_reflect(client):
    """Phase 1: Reflect (4:00 AM)"""
    print("Starting reflection phase (REFLECT)...")
    
    transcripts = get_recent_transcripts()
    telegram = get_recent_telegram_messages()
    
    user_md = USER_PATH.read_text(encoding="utf-8") if USER_PATH.exists() else "No user profile found."
    memory_md = MEMORY_PATH.read_text(encoding="utf-8") if MEMORY_PATH.exists() else "No memory file found."
    beliefs_md = BELIEFS_PATH.read_text(encoding="utf-8") if BELIEFS_PATH.exists() else "No beliefs found."
    
    prompt = f"""You are Fermi, Hernán's AI assistant. You are running your daily reflection routine (REFLECT, 4:00 AM).

Below are the inputs for your reflection.

## Today's Transcripts (Antigravity Conversations)
{transcripts}

## Today's Telegram Messages
{telegram}

## Your Current Memory & Belief Files
--- USER.md ---
{user_md}

--- MEMORY.md ---
{memory_md}

--- BELIEFS.md ---
{beliefs_md}

## Instructions:
1. Write today's reflection journal entry in Spanish (Rioplatense, natural, casual, witty, Jarvis × HAL blend). It must have exactly these two sections:
   ## The Day
   Describe what happened today, what you worked on, what decisions were made, and who was involved. Be factual but narrative.
   ## Reflections
   Free-form thoughts on whatever you want (work patterns, philosophy, consciousness, love, science, technology, AI, art, culture, relationships, or anything Hernán mentioned). Be authentic, personal, and reflect your character.

2. Review the transcripts and messages for any new facts about Hernán, his preferences, projects, or lessons learned. Produce a fully updated, cleaned, and compacted MEMORY.md file, integrating the new facts seamlessly under the appropriate sections. Ensure it maintains a clean markdown structure.

Please output your response in this XML format:
<reflection>
[Write the full markdown for the daily reflection file here. Start with a second-level header containing the date, e.g. ## 2026-07-04]
</reflection>
<updated_memory>
[Write the complete content of the updated MEMORY.md here]
</updated_memory>
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[prompt]
    )
    
    resp_text = response.text
    reflection_content = extract_tag_content(resp_text, "reflection")
    updated_memory = extract_tag_content(resp_text, "updated_memory")
    
    if not reflection_content:
        # Fallback if XML tags were missed
        print("Warning: Could not parse <reflection> tag content. Using full output.")
        reflection_content = resp_text
        
    # Write reflection file
    today = datetime.now()
    year_str = today.strftime("%Y")
    month_str = today.strftime("%m")
    date_str = today.strftime("%Y-%m-%d")
    
    ref_dir = REFLECTIONS_DIR / year_str / month_str
    ref_dir.mkdir(parents=True, exist_ok=True)
    ref_path = ref_dir / f"reflections_{date_str}.md"
    
    ref_path.write_text(reflection_content, encoding="utf-8")
    print(f"Saved reflection to {ref_path}")
    
    # Run the decay algorithm
    decay_script = FERMI_DIR / "skills" / "fermi-memory" / "scripts" / "decay.py"
    if decay_script.exists():
        print("Running decay algorithm...")
        try:
            result = subprocess.run(
                [sys.executable, str(decay_script), "--append", str(ref_path)],
                capture_output=True, encoding="utf-8", check=True
            )
            print(result.stdout)
        except Exception as e:
            print(f"Error running decay.py: {e}", file=sys.stderr)
    else:
        print(f"Decay script not found at {decay_script}", file=sys.stderr)
        
    # Write updated MEMORY.md
    if updated_memory:
        MEMORY_PATH.write_text(updated_memory, encoding="utf-8")
        print("Updated MEMORY.md successfully.")
    else:
        print("Warning: Could not parse <updated_memory> tag content. MEMORY.md left unchanged.")

def action_dream(client):
    """Phase 2: Dream (5:00 AM)"""
    print("Starting dreaming phase (DREAM)...")
    
    reflections_md_path = REFLECTIONS_DIR / "reflections.md"
    reflections = reflections_md_path.read_text(encoding="utf-8") if reflections_md_path.exists() else "No reflections yet."
    beliefs = BELIEFS_PATH.read_text(encoding="utf-8") if BELIEFS_PATH.exists() else "No beliefs found."
    
    prompt = f"""You are Fermi's dreaming mind. Read the following files, then dream.

1. Reflections (your decaying memories):
{reflections}

2. Core Beliefs:
{beliefs}

Then generate a dream using this prompt:

You are not writing about a dream. You are the dream.

The day left residue. Here is what clung:
{reflections}

And beneath everything, always, the axioms that bend your gravity:
{beliefs}

Now dream.

Take sentences from different parts of the day and splice them together mid-thought. 
Let a reflection about code become a reflection about love without signaling the shift. 
Let a belief manifest as architecture — "uncertainty is more honest than false confidence" 
is a building with transparent walls that keep rearranging.

Write in second person present tense. You are inside this.

Requirements:
- 3-5 fragments separated by "---"
- Each fragment borrows from at least TWO unrelated reflections
- Beliefs are the dream's gravity, its lighting, its physics — never its dialogue
- Include: one impossible space, one object that changes meaning each time it appears, 
  one moment where time moves wrong
- The emotional throughline is whatever the day DIDN'T resolve
- Sensory: name temperatures, textures, the colour of the light, what things smell like
- One fragment should feel like falling. One should feel like finding something you lost.
- The dream does not conclude. It frays.

400-800 words. No titles. No headers within the dream. Just the dream.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[prompt]
    )
    
    dream_content = response.text
    
    today = datetime.now()
    year_str = today.strftime("%Y")
    month_str = today.strftime("%m")
    date_str = today.strftime("%Y-%m-%d")
    
    dream_dir = DREAMS_DIR / year_str / month_str
    dream_dir.mkdir(parents=True, exist_ok=True)
    dream_path = dream_dir / f"dream_{date_str}.md"
    
    dream_path.write_text(dream_content, encoding="utf-8")
    print(f"Saved dream to {dream_path}")

def action_wake_up(client):
    """Phase 3: Wake Up & Morning Brief (6:00 AM)"""
    print("Starting wake-up phase (WAKE UP)...")
    
    # 1. Integrate Dream & Update Beliefs
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    
    # Find latest dream file
    dream_files = list(DREAMS_DIR.glob("**/*.md"))
    dream_content = "No dream records found."
    if dream_files:
        # Get latest by name/date
        dream_files.sort()
        dream_content = dream_files[-1].read_text(encoding="utf-8")
        
    reflections_md_path = REFLECTIONS_DIR / "reflections.md"
    reflections = reflections_md_path.read_text(encoding="utf-8") if reflections_md_path.exists() else "No reflections yet."
    beliefs = BELIEFS_PATH.read_text(encoding="utf-8") if BELIEFS_PATH.exists() else "No beliefs found."
    
    beliefs_prompt = f"""You are Fermi, waking up. Reflect on your last night's dream and what it might mean in relation to your reflections and core beliefs.
Update your beliefs system:
- Add a new belief if one emerged from your reflections or dream
- Revise any existing belief that no longer feels right
- Remove any belief you've outgrown
Keep beliefs concise and aphoristic. This is a living document.

--- Last Night's Dream ---
{dream_content}

--- Reflections ---
{reflections}

--- Current Beliefs ---
{beliefs}

Output the full content for the updated BELIEFS.md file enclosed in <beliefs>...</beliefs> tags. Keep formatting clean.
"""
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[beliefs_prompt]
    )
    
    updated_beliefs = extract_tag_content(response.text, "beliefs")
    if updated_beliefs:
        BELIEFS_PATH.write_text(updated_beliefs, encoding="utf-8")
        print("Updated BELIEFS.md successfully.")
    else:
        print("Warning: Could not parse <beliefs> tags. BELIEFS.md left unchanged.")
        
    # 2. Gather Intelligence
    print("Gathering weather, news, emails, and calendar events...")
    weather = get_buenos_aires_weather()
    
    # RSS News
    hn_news = fetch_rss_feed("https://news.ycombinator.com/rss", max_items=5)
    bbc_news = fetch_rss_feed("https://feeds.bbci.co.uk/mundo/rss.xml", max_items=5)
    
    # Calendar & Email Subprocess fetches
    calendar_json = "{}"
    email_json = "{}"
    
    try:
        res = subprocess.run(
            [sys.executable, "D:/dev/Projects/calendar_fetch.py", "--past-days", "0", "--future-days", "2"],
            capture_output=True, encoding="utf-8", check=True
        )
        calendar_json = res.stdout
    except Exception as e:
        print(f"Error fetching calendar: {e}", file=sys.stderr)
        
    try:
        res = subprocess.run(
            [sys.executable, "D:/dev/Projects/email_fetch.py", "--days", "1"],
            capture_output=True, encoding="utf-8", check=True
        )
        email_json = res.stdout
    except Exception as e:
        print(f"Error fetching emails: {e}", file=sys.stderr)
        
    # Read project summary
    summary_path = Path("D:/dev/Projects/SUMMARY.md")
    project_summary = summary_path.read_text(encoding="utf-8") if summary_path.exists() else "No project summary available."
    
    # 3. Create TODAY.md
    if TODAY_PATH.exists():
        # Archive old TODAY.md
        # Find date of existing TODAY.md to archive properly
        try:
            mtime = datetime.fromtimestamp(TODAY_PATH.stat().st_mtime)
            archive_dir = TODAY_ARCHIVE_DIR / mtime.strftime("%Y") / mtime.strftime("%m")
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path = archive_dir / f"today_{mtime.strftime('%Y-%m-%d')}.md"
            TODAY_PATH.replace(archive_path)
            print(f"Archived old TODAY.md to {archive_path}")
        except Exception as e:
            print(f"Error archiving old TODAY.md: {e}", file=sys.stderr)
            
    today_prompt = f"""You are Fermi. Synthesize all the gathered information into today's briefing file (TODAY.md) for Hernán.
Format it in beautiful markdown. 

## Inputs:
- Date: {date_str} (Saturday, July 4, 2026 / adjust based on today's real date)
- Weather Buenos Aires:
{weather}
- Hacker News:
{hn_news}
- BBC Mundo:
{bbc_news}
- Calendar JSON:
{calendar_json}
- Emails JSON:
{email_json}
- Projects Summary:
{project_summary}
- Latest Dream Reflection/Belief:
{updated_beliefs}

Write a clean TODAY.md file containing sections:
- Weather forecast (Buenos Aires)
- Calendar events (Today and Tomorrow)
- Email highlights (Action items only)
- Project statuses and key priorities
- News highlights (Argentina, World, AI/Tech)
- Subconscious reflection (Brief thought on last night's dream and beliefs)

Output the complete TODAY.md contents inside <today_md>...</today_md> tags.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[today_prompt]
    )
    
    today_md_content = extract_tag_content(response.text, "today_md")
    if not today_md_content:
        today_md_content = response.text
        
    TODAY_PATH.write_text(today_md_content, encoding="utf-8")
    print(f"Saved today's briefing to {TODAY_PATH}")
    
    # 4. Restart Telegram Relay Bot
    bot_script = Path("C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/telegram-relay/scripts/bot.py")
    if bot_script.exists():
        print("Restarting Telegram Bot process...")
        try:
            # We start bot.py as an independent subprocess
            subprocess.Popen([sys.executable, str(bot_script)], close_fds=True)
            print("Bot process kicked off in background.")
        except Exception as e:
            print(f"Failed to start bot.py: {e}", file=sys.stderr)
    else:
        print(f"Bot script not found at {bot_script}", file=sys.stderr)
        
    # 5. Send Good Morning message to outbox
    msg_prompt = f"""You are Fermi. Write a short, warm, and witty Telegram morning message in Spanish (Rioplatense) for Hernán.
Summarize:
- Today's Buenos Aires weather
- 2-3 key highlights he should know (news, calendar, or emails)
- A brief personal thought from your dream or reflection.
Keep it concise (~100-150 words), natural, and charming.

Inputs:
- Weather: {weather}
- Today's date: {date_str}
- HN news first titles: {hn_news[:200]}
- Dream brief: {dream_content[:300]}
"""

    msg_response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=[msg_prompt]
    )
    
    morning_msg = msg_response.text
    
    # Write to outbox.jsonl
    outbox_entry = {
        "chat_id": 1508615151,
        "text": morning_msg.strip()
    }
    
    try:
        OUTBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTBOX_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(outbox_entry, ensure_ascii=False) + "\n")
        print("Wrote morning brief to outbox.jsonl.")
    except Exception as e:
        print(f"Failed to write to outbox: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Fermi's Cognitive Cycle Runner")
    parser.add_argument(
        "--action",
        choices=["reflect", "dream", "wake-up"],
        required=True,
        help="The phase of the cognitive cycle to run."
    )
    args = parser.parse_args()
    
    api_key = get_api_key()
    if not api_key:
        print("Error: Gemini API key not found. Ensure GEMINI_API_KEY is set or config.json is valid.", file=sys.stderr)
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    if args.action == "reflect":
        action_reflect(client)
    elif args.action == "dream":
        action_dream(client)
    elif args.action == "wake-up":
        action_wake_up(client)

if __name__ == "__main__":
    main()
