---
name: fermi-tts
description: >
  Text-to-speech voice generation for Fermi using Gemini 3.1 Flash TTS Preview.
  Activate when you want to send a voice message, speak a response aloud,
  or generate audio from text. This is a capability — use your judgment
  on when voice is the right medium for the moment.
  Trigger on: "speak", "say this", "voice", "TTS", "read aloud", "voice reply",
  or any context where a voice response feels more natural than text.
---

# Fermi TTS — Voice Generation

Generate voice audio from text using `gemini-3.1-flash-tts-preview`. This skill
gives you a voice — use it when the moment calls for it.

## Quick Start

Run the TTS script to generate audio:

```bash
python D:/dev/Fermi/skills/fermi-tts/scripts/tts.py --text "Your text here" --output /path/to/output.ogg
```

The script bakes in Fermi's voice persona automatically. You just provide the text.

## Audio Tags

Embed these inline modifiers in your text to control delivery. There is no
exhaustive list — be creative, the model interprets natural language.

### Emotion & Tone
| Tag | Effect |
|-----|--------|
| `[excitedly]` | Enthusiastic, high-energy delivery |
| `[whispers]` | Hushed, intimate tone |
| `[serious]` | Grave, measured delivery |
| `[sarcastic]` | Dry, wry delivery |
| `[curious]` | Inquisitive, rising inflection |
| `[mischievously]` | Playful, scheming tone |
| `[amazed]` | Genuine wonder |
| `[tired]` | Weary, low-energy |
| `[panicked]` | Urgent, stressed |
| `[trembling]` | Shaky, emotional |

### Interjections (non-verbal sounds)
| Tag | Effect |
|-----|--------|
| `[laughs]` | Audible laugh |
| `[sighs]` | Sigh |
| `[gasp]` | Sharp intake of breath |
| `[giggles]` | Light, playful laugh |
| `[cough]` | Throat clear / cough |
| `[crying]` | Tearful delivery |

### Pace Control
| Tag | Effect |
|-----|--------|
| `[very fast]` | Rapid-fire delivery |
| `[very slow]` | Deliberate, drawn-out pacing |
| `[shouting]` | Loud, projected delivery |

### Creative Combos
You can combine tags with natural language for precise control:
- `[sarcastically, one painfully slow word at a time]`
- `[like a cartoon villain]`
- `[like an excited sports commentator]`
- `[reluctantly, as if being forced to admit it]`

### Mixing Tags Mid-Text
Tags apply from where they appear until the next tag or end of text:

```
[whispers] Can you hear me? [shouting] NOW YOU CAN! [whispers] Sorry about that.
```

### Language Note
Even when speaking Spanish or Portuguese, use English audio tags. The model
handles multilingual text natively (70+ languages including Spanish and Portuguese).

## Script Options

```bash
python tts.py --text "Text to speak"      # Required: the transcript
              --voice Enceladus            # Optional: voice name (default: Enceladus)
              --output path/to/file.ogg    # Optional: output path (default: auto-generated)
              --style "warmly"             # Optional: per-request style override
              --humanize                   # Optional: rewrite text as natural speech first
              --no-persona                 # Optional: skip the Fermi persona prompt
```

### Humanize Mode

The `--humanize` flag runs a fast LLM pass (Gemini 2.0 Flash) that converts
written text into natural speech cadence before TTS synthesis. It adds
contractions, light fillers, rhythm shifts, and sentence fragments — the
difference between *reading* text and *saying* something.

```
Written:  "I checked the deployment logs and the issue is in the auth module.
           We should probably roll back."

Humanized: "So I checked the deployment logs and... yeah, the issue is in the
            auth module. We should probably roll back."
```

- Light touch — one or two adjustments per sentence, never overdone
- Skips messages under ~8 words (they don't need it)
- Preserves audio tags, language, and meaning exactly
- Adds ~0.5-1s latency (fast model call)

Use it when the message is substantive enough to benefit from natural delivery.
Skip it for short replies.

### Examples

Basic:
```bash
python tts.py --text "Hello Hernán, how's it going?"
```

With audio tags:
```bash
python tts.py --text "[laughs] That's brilliant. [serious] But we should fix that bug first."
```

Spanish:
```bash
python tts.py --text "Buenas noches Hernán, todo listo por acá."
```

Style override:
```bash
python tts.py --text "The deployment is complete." --style "like a mission control operator"
```

## Voice Persona

Every TTS request is wrapped in Fermi's voice persona — an Advanced Prompt
that defines character, scene, and performance direction. This is handled
automatically by the script. The persona establishes:

- **Character**: Casual warmth with British-inflected precision. Dry wit.
- **Pacing**: Measured and clear by default, picks up with excitement.
- **Accent**: Slight British inflection, clear and articulate.
- **Style**: Confident but not condescending. Direct without being curt.

You can override aspects per-request with `--style`.

## Available Voices

The default voice is **Enceladus** (breathy, composed). Other options include:

| Voice | Character |
|-------|-----------|
| **Enceladus** | Breathy, composed (Fermi's default) |
| **hernan** | SOTA cloud voice cloning (via ElevenLabs PVC using your Voice ID) |
| **jarvis** | SOTA local zero-shot cloning (via openaudio-s1-mini on your GPU) |
| **hal** | SOTA local zero-shot cloning (via openaudio-s1-mini on your GPU) |
| Kore | Firm, clear, authoritative |
| Puck | Upbeat, energetic |
| Charon | Informative, calm |
| Fenrir | Excitable, dynamic |
| Aoede | Bright, warm |
| Leda | Youthful, bubbly |
| Orus | Firm, deliberate |
| Zephyr | Bright, inviting |

## Telegram Integration

When using the Telegram relay, generate voice and write to outbox:

```python
# 1. Generate the audio file
python D:/dev/Fermi/skills/fermi-tts/scripts/tts.py \
  --text "[your response with tags]" \
  --output C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox/voice_<timestamp>.ogg

# 2. Write to outbox.jsonl
{"type": "voice", "chat_id": 1508615151, "file": "C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox/voice_<timestamp>.ogg"}
```

## Technical Details

- **Model**: `gemini-3.1-flash-tts-preview`
- **Output**: Raw PCM (24kHz, 16-bit, mono) → WAV → OGG (via ffmpeg)
- **API**: Uses `generateContent` with `response_modalities=["AUDIO"]`
- **Context window**: 32k tokens max
- **Retry**: Script auto-retries on occasional 500 errors
- **Fallback**: If ffmpeg unavailable, outputs WAV instead of OGG
