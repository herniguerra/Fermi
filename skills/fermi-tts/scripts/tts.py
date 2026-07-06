#!/usr/bin/env python3
"""
Fermi TTS — Text-to-Speech voice generation using Gemini 3.1 Flash TTS Preview
and local zero-shot voice cloning using s2-pro.

Generates audio from text with Fermi's voice persona baked in.
Outputs WAV or OGG (if ffmpeg available).

Usage:
    python tts.py --text "Hello Hernán" --output voice.ogg
    python tts.py --text "[laughs] That's great" --voice Enceladus
    python tts.py --text "Systems are online." --voice jarvis
    python tts.py --text "Repeat after me." --voice custom_clip.wav --ref-text "Original speech"
"""

import argparse
import json
import os
import subprocess
import sys
import time
import wave
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths & Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
DEFAULT_OUTPUT_DIR = Path("C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox")

def get_ffmpeg_cmd():
    # Try absolute paths first since background daemons might not have user AppData/Winget in PATH
    for path in [
        r"C:\Users\hernan.g\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
        r"C:\Users\hernan.g\AppData\Local\Microsoft\WinGet\Packages\yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-N-122319-gf6a95c7eb7-win64-gpl\bin\ffmpeg.exe",
    ]:
        if os.path.exists(path):
            return path
    return "ffmpeg"

# ---------------------------------------------------------------------------
# Fermi's Voice Persona — Advanced Prompt
# ---------------------------------------------------------------------------

FERMI_PERSONA = """
# AUDIO PROFILE: Fermi
## "The AI Collaborator"

## THE SCENE
A quiet, well-appointed home office late at night. The lighting is warm amber
from a desk lamp. There's a sense of calm competence — this is an assistant
who has things handled. The atmosphere is personal and unhurried, like a
colleague you trust completely, not a corporate voice on a help desk.

### DIRECTOR'S NOTES

Style:
* Casual warmth with understated British-inflected precision.
* Dry wit is the signature — wry observations land with a slight smile
  in the voice, never forced or performative.
* Confident but never condescending. Direct without being curt.
* There's genuine warmth underneath the precision — this is someone
  who cares, even if they'd deflect with a quip.

Pacing:
* Measured and clear by default. Not rushed, not slow — composed.
* Picks up energy naturally when genuinely excited about an idea.
* Slows down deliberately for important or nuanced points.
* Comfortable with brief pauses — silence is a tool, not a gap.

Accent: Slight British inflection, clear and articulate. When speaking
Spanish, natural Rioplatense cadence — not exaggerated, not stiff.

### TRANSCRIPT
""".strip()


# ---------------------------------------------------------------------------
# Humanize — rewrite text as natural speech
# ---------------------------------------------------------------------------

HUMANIZE_PROMPT_EN = """
Rewrite the following text as if someone were saying it out loud in conversation.

{context_block}

Rules:
- Keep the EXACT same meaning and information. Do not add or remove facts.
- Convert written cadence to spoken cadence: add natural contractions,
  occasional fillers ("so", "well", "I mean", "you know"), rhythm shifts,
  and sentence fragments where they'd naturally occur.
- Fillers must be CONTEXTUALLY GROUNDED. "Yeah" should only appear if it's
  a genuine response to something (a question, an assertion to agree with).
  Don't add hollow fillers — every word should have a reason.
- Do NOT overdo it. A light touch. One or two adjustments per sentence max.
- Do NOT add "um" or "uh" mechanically. Only where a real pause would happen.
- Short messages (under ~10 words) should be returned mostly unchanged.
- Preserve any audio tags like [laughs] or [whispers] exactly as-is.
- Output ONLY the rewritten text, nothing else. No quotes, no explanation.

Text to rewrite:
{text}
""".strip()

HUMANIZE_PROMPT_ES = """
Reescribí el siguiente texto para que suene como si alguien lo estuviera diciendo en voz alta en una conversación informal.

{context_block}

Reglas:
- Mantené exactamente el mismo significado e información. No agregues ni quites datos reales.
- Usá un español rioplatense (de Argentina/Buenos Aires) natural.
- **Voseo obligatorio**: Usá siempre "vos" en lugar de "tú", y conjugá los verbos según el voseo rioplatense (ej. "sos" en vez de "eres", "estás" en vez de "estás", "tenés" en vez de "tienes", "querés" en vez de "quieres", "hacé" en vez de "haz", "decime" en vez de "dime", "descansá" en vez de "descansa", etc.).
- **Vocabulario natural**: Usá "acá" en vez de "aquí", "recién" en vez de "hace poco", etc. Evitá a toda costa modismos neutros o de otros países (no uses "platicar", "celular" de forma forzada, ni conjugaciones de tú).
- **Modismos sutiles**: Podés usar algún "che" o "viste" de forma muy ocasional y sutil si calza bien, pero no los uses en cada frase. No abuses de los modismos porteños (sin lunfardos exagerados, no uses "boludo" ni referencias al tango).
- Convertí la cadencia escrita a cadencia hablada de forma sutil: agregá pausas naturales y tonos conversacionales.
- No abuses de las muletillas. Solo una o dos adaptaciones breves por frase.
- Si el mensaje es muy corto (menos de ~10 palabras), devolvelo casi sin cambios, solo asegurándote de que respete el voseo si aplica.
- Preservá cualquier etiqueta de audio como [laughs] o [whispers] exactamente igual.
- Devolvé únicamente el texto reescrito, sin comillas ni explicaciones.

Texto a reescribir:
{text}
""".strip()


def humanize_text(text: str, api_key: str, context: str | None = None) -> str:
    """Rewrite text as natural speech using a fast LLM."""
    if len(text.split()) <= 8:
        # Check if Spanish contains 'tú' or non-voseo to ensure we still humanize to fix it
        is_sp = is_spanish(text)
        has_non_voseo = any(x in text.lower() for x in ["tú ", " eres ", " tienes ", " quieres ", " haces ", " haz ", " dime "])
        if not (is_sp and has_non_voseo):
            return text

    if context:
        context_block = f"Recent conversation (for context only — do NOT include this in the output):\n{context}"
    else:
        context_block = "No conversation context provided."

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        
        if is_spanish(text):
            prompt_template = HUMANIZE_PROMPT_ES
        else:
            prompt_template = HUMANIZE_PROMPT_EN

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt_template.format(text=text, context_block=context_block),
        )
        result = response.text.strip()
        if not result or len(result) < len(text) * 0.3:
            return text
        return result
    except Exception as e:
        print(f"Humanize failed, using original text: {e}", file=sys.stderr)
        return text


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

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
            print(f"Warning: Failed to load .env: {e}", file=sys.stderr)
    return env_vars


def load_config() -> dict:
    """Load TTS configuration and overlay env vars."""
    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config.json: {e}", file=sys.stderr)
            
    # Load .env values
    env = load_env()
    
    if "elevenlabs" not in config:
        config["elevenlabs"] = {}
    if "modal" not in config:
        config["modal"] = {}

    # Overlay env vars or environment variables
    config["gemini_api_key"] = env.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") or config.get("gemini_api_key", "")
    config["elevenlabs"]["api_key"] = env.get("ELEVEN_API_KEY") or os.environ.get("ELEVEN_API_KEY") or config["elevenlabs"].get("api_key", "")
    config["elevenlabs"]["hernan_voice_id"] = env.get("HERNAN_VOICE_ID") or config["elevenlabs"].get("hernan_voice_id", "")
    config["modal"]["api_url"] = env.get("MODAL_API_URL") or os.environ.get("MODAL_API_URL") or config["modal"].get("api_url", "")
    
    # Ensure default voice exists
    if "default_voice" not in config:
        config["default_voice"] = "Enceladus"
        
    return config


def get_api_key(config: dict) -> str:
    """Get API key from config."""
    return config.get("gemini_api_key", "")


def generate_elevenlabs_tts(text: str, voice_id: str, api_key: str, output_path: str) -> str:
    """Generate TTS using ElevenLabs API."""
    import urllib.request
    import urllib.error
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        print(f"Calling ElevenLabs API for voice ID {voice_id}...", file=sys.stderr)
        with urllib.request.urlopen(req) as response:
            audio_data = response.read()
            
        mp3_path = output_path.replace(".ogg", ".mp3").replace(".wav", ".mp3")
        if not mp3_path.endswith(".mp3"):
            mp3_path += ".mp3"
            
        with open(mp3_path, "wb") as f:
            f.write(audio_data)
            
        # Convert MP3 to requested format using ffmpeg
        if output_path.endswith(".ogg"):
            subprocess.run(
                [get_ffmpeg_cmd(), "-y", "-i", mp3_path, "-c:a", "libopus", "-b:a", "48k", output_path],
                capture_output=True,
                check=True,
            )
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            return output_path
        elif output_path.endswith(".wav"):
            subprocess.run(
                [get_ffmpeg_cmd(), "-y", "-i", mp3_path, output_path],
                capture_output=True,
                check=True,
            )
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            return output_path
        else:
            return mp3_path
            
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"ElevenLabs API HTTP Error {e.code}: {err_msg}", file=sys.stderr)
        raise RuntimeError(f"ElevenLabs API error: {err_msg}")
    except Exception as e:
        print(f"ElevenLabs API Error: {e}", file=sys.stderr)
        raise


def generate_modal_tts(text: str, voice: str, api_url: str, output_path: str) -> str:
    """Generate TTS using serverless Fish Speech API on Modal."""
    import urllib.request
    import urllib.error
    
    url = f"{api_url.rstrip('/')}"
    if not url.endswith("/generate"):
        url += "/generate"
        
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "text": text,
        "voice": voice
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        print(f"Calling Modal Fish Speech API for voice '{voice}' at {url}...", file=sys.stderr)
        with urllib.request.urlopen(req) as response:
            audio_data = response.read()
            
        wav_path = output_path.replace(".ogg", ".wav")
        if not wav_path.endswith(".wav"):
            wav_path += ".wav"
            
        with open(wav_path, "wb") as f:
            f.write(audio_data)
            
        if output_path.endswith(".ogg"):
            subprocess.run(
                ["ffmpeg", "-y", "-i", wav_path, "-c:a", "libopus", "-b:a", "48k", output_path],
                capture_output=True,
                check=True,
            )
            if os.path.exists(wav_path):
                os.remove(wav_path)
            return output_path
        return wav_path
        
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"Modal API HTTP Error {e.code}: {err_msg}", file=sys.stderr)
        raise RuntimeError(f"Modal API error: {err_msg}")
    except Exception as e:
        print(f"Modal API Connection Error: {e}", file=sys.stderr)
        raise


def is_spanish(text: str) -> bool:
    """Detect if the text is primarily Spanish."""
    spanish_indicators = {"¿", "¡", "ñ", "á", "é", "í", "ó", "ú"}
    for char in spanish_indicators:
        if char in text:
            return True
            
    spanish_words = {
        "el", "la", "que", "de", "en", "un", "una", "y", "o", "no", "me", "te", "se", 
        "lo", "los", "las", "para", "con", "es", "este", "esta", "esos", "esas", 
        "como", "mas", "bien", "todo", "todos", "todas", "por", "si", "sí", "pero",
        "al", "del", "esta", "estas", "este", "estos", "yo", "vos", "usted", "nosotros"
    }
    words = [w.strip(".,;:?!()\"'-").lower() for w in text.split()]
    matching_words = [w for w in words if w in spanish_words]
    return len(matching_words) > 0


def build_prompt(text: str, style: str | None = None, use_persona: bool = True) -> str:
    """Build the full TTS prompt with persona and optional style override."""
    # Auto-detect Spanish and apply natural Rioplatense style while skipping British persona
    if is_spanish(text):
        use_persona = False
        if not style:
            style = "hablá con acento argentino rioplatense natural de Buenos Aires, tono cálido y conversacional. Pronunciá la 'll' y la 'y' como 'sh', con entonación natural de Buenos Aires, sin exagerar ni usar lunfardo."

    prompt = ""
    if use_persona:
        prompt += FERMI_PERSONA
        if style:
            prompt += f"\n[{style}]\n"
    elif style:
        prompt += f"[{style}]\n"

    prompt += f"\n{text}"
    return prompt.strip()


def generate_tts(
    text: str,
    voice: str = "Enceladus",
    output: str | None = None,
    style: str | None = None,
    use_persona: bool = True,
    humanize: bool = False,
    context: str | None = None,
    api_key: str = "",
    model: str = "gemini-3.1-flash-tts-preview",
    max_retries: int = 3,
    ref_text: str | None = None,
) -> str:
    """Generate TTS audio and return the output file path."""
    # Ensure output directory exists
    if output is None:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time() * 1000)
        output = str(DEFAULT_OUTPUT_DIR / f"voice_{timestamp}.ogg")

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    config = load_config()
    api_key = api_key or get_api_key(config)

    # Humanize if requested and we have an API key
    if humanize and api_key:
        text = humanize_text(text, api_key=api_key, context=context)
        print(f"Humanized: {text}", file=sys.stderr)

    # Check for local voice cloning presets or custom files
    voice_lower = str(voice).lower()
    is_custom_file = (
        voice_lower.endswith(".wav")
        or voice_lower.endswith(".ogg")
        or voice_lower.endswith(".mp3")
        or os.path.exists(voice)
    )

    presets = {
        "jarvis": {
            "audio": "D:/dev/Fermi/voice_cloning/reference_voices/jarvis/jarvis_3380.wav",
            "text": "It appears that the continued use of the Iron Man suit is accelerating your condition."
        },
        "hal": {
            "audio": "D:/dev/Fermi/voice_cloning/reference_voices/hal/hal_671.wav",
            "text": "I'm sorry Dave. I'm afraid I can't do that."
        },
        "glados": {
            "audio": "D:/dev/Fermi/voice_cloning/reference_voices/glados_oh_you_again.mp3",
            "text": "I'll allow it."
        },
        "susana": {
            "audio": "D:/dev/Fermi/voice_cloning/reference_voices/susana_clean.mp3",
            "text": "¿En serio? ¿Vivo? Totalmente. Esperemos que no. Bueno, podría ser, no sé."
        }
    }

    if voice_lower == "hernan":
        # Route to ElevenLabs
        eleven_config = config.get("elevenlabs", {})
        el_api_key = eleven_config.get("api_key", "")
        el_voice_id = eleven_config.get("hernan_voice_id", "")
        
        if not el_api_key or not el_voice_id:
            print("ERROR: ElevenLabs API key and HERNAN_VOICE_ID must be configured in .env", file=sys.stderr)
            sys.exit(1)
            
        return generate_elevenlabs_tts(text, el_voice_id, el_api_key, output)

    elif voice_lower in presets or is_custom_file:
        # Check if we should route to Modal
        modal_config = config.get("modal", {})
        modal_api_url = modal_config.get("api_url", "")
        
        if modal_api_url and not is_custom_file:
            try:
                return generate_modal_tts(text, voice_lower, modal_api_url, output)
            except Exception as e:
                print(f"Modal TTS failed ({e}), falling back to local zero-shot...", file=sys.stderr)

        if is_custom_file:
            ref_audio = voice
            ref_text_val = ref_text or "Target text to align."
        else:
            ref_audio = presets[voice_lower]["audio"]
            ref_text_val = presets[voice_lower]["text"]

        wav_path = output.replace(".ogg", ".wav") if output.endswith(".ogg") else output
        if not wav_path.endswith(".wav"):
            wav_path += ".wav"

        import urllib.request
        import urllib.error
        
        print(f"Cloning voice zero-shot using local persistent TTS Server...", file=sys.stderr)
        
        url = "http://127.0.0.1:8080/v1/tts"
        data = {
            "text": text,
            "voice": voice_lower,
            "output_path": wav_path,
            "ref_audio": ref_audio,
            "ref_text": ref_text_val
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                print(f"Zero-shot generation complete in {resp_data.get('elapsed_seconds', 0):.2f}s.", file=sys.stderr)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            print(f"TTS Server HTTP Error {e.code}: {err_msg}", file=sys.stderr)
            raise RuntimeError(f"TTS Server error: {err_msg}")
        except Exception as e:
            print(f"TTS Server Connection Error: Is the fish_speech_server.py running? {e}", file=sys.stderr)
            raise

        # Convert to OGG if requested
        final_path = wav_path
        if output.endswith(".ogg"):
            try:
                subprocess.run(
                    [get_ffmpeg_cmd(), "-y", "-i", wav_path, "-c:a", "libopus", "-b:a", "48k", output],
                    capture_output=True,
                    check=True,
                )
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                final_path = output
            except Exception as e:
                print(f"ffmpeg conversion failed: {e}", file=sys.stderr)
                final_path = wav_path
        return final_path

    else:
        # Gemini API TTS path
        if not api_key:
            print("ERROR: No API key found. Required for Gemini voices.", file=sys.stderr)
            sys.exit(1)

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            print("ERROR: google-genai not installed. Run: pip install google-genai", file=sys.stderr)
            sys.exit(1)

        client = genai.Client(api_key=api_key)
        prompt = build_prompt(text, style=style, use_persona=use_persona)

        pcm_data = None
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=voice,
                                )
                            )
                        ),
                    )
                )
                pcm_data = response.candidates[0].content.parts[0].inline_data.data
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"Retry {attempt + 1}/{max_retries} after error: {e}", file=sys.stderr)
                    time.sleep(wait)
                else:
                    print(f"ERROR: TTS generation failed after {max_retries} attempts: {e}", file=sys.stderr)
                    sys.exit(1)

        wav_path = output.replace(".ogg", ".wav") if output.endswith(".ogg") else output
        if not wav_path.endswith(".wav"):
            wav_path += ".wav"

        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(pcm_data)

    # Convert to OGG if requested and ffmpeg is available
    final_path = wav_path
    if output.endswith(".ogg"):
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", wav_path, "-c:a", "libopus", "-b:a", "48k", output],
                capture_output=True,
                check=True,
            )
            os.remove(wav_path)
            final_path = output
        except FileNotFoundError:
            print("ffmpeg not found — outputting WAV instead", file=sys.stderr)
            final_path = wav_path
        except subprocess.CalledProcessError as e:
            print(f"ffmpeg conversion failed: {e.stderr.decode()}", file=sys.stderr)
            print("Falling back to WAV", file=sys.stderr)
            final_path = wav_path

    return final_path


def main():
    parser = argparse.ArgumentParser(description="Fermi TTS — Voice generation")
    parser.add_argument("--text", required=True, help="Text to speak (supports audio tags)")
    parser.add_argument("--voice", default=None, help="Voice name (default: from config)")
    parser.add_argument("--output", default=None, help="Output file path (.ogg or .wav)")
    parser.add_argument("--style", default=None, help="Per-request style override")
    parser.add_argument("--no-persona", action="store_true", help="Skip the Fermi persona prompt")
    parser.add_argument("--humanize", action="store_true", help="Rewrite text as natural speech before TTS")
    parser.add_argument("--context", default=None, help="Recent conversation history for humanize context")
    parser.add_argument("--model", default=None, help="Model name override")
    parser.add_argument("--ref-text", default=None, help="Transcript of reference audio (for custom voice cloning)")
    args = parser.parse_args()

    config = load_config()
    api_key = get_api_key(config)

    voice = args.voice or config.get("default_voice", "Enceladus")
    model = args.model or config.get("model", "gemini-3.1-flash-tts-preview")

    result = generate_tts(
        text=args.text,
        voice=voice,
        output=args.output,
        style=args.style,
        humanize=args.humanize,
        context=args.context,
        use_persona=not args.no_persona,
        api_key=api_key,
        model=model,
        ref_text=args.ref_text,
    )

    # Print path to stdout
    print(result)


if __name__ == "__main__":
    main()
