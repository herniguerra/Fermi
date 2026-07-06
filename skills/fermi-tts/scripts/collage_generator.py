#!/usr/bin/env python3
import sys
import os
import wave
import subprocess
import time
from pathlib import Path

# Add script directory to path to import tts
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
import tts
print(f"DEBUG: imported tts from {tts.__file__}", file=sys.stderr)
# We can find presets inside generate_tts function, or we can check presets in local scope if tts.py exposes it.
# Wait, presets is local to generate_tts inside tts.py, so it's not a module-level variable. That's fine, we can just print the imported file path.
from tts import generate_tts, get_ffmpeg_cmd

def standardize_wav(input_path, output_path):
    """Standardize WAV file to 24000Hz, mono, 16-bit PCM."""
    cmd = [
        get_ffmpeg_cmd(),
        "-y",
        "-i", str(input_path),
        "-ar", "24000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def main():
    segments = [
        {
            "voice": "Enceladus",
            "text": "Entendido, Herni. Usar las voces con intención y no al azar.",
            "style": "natural Argentine Rioplatense accent, warm conversational tone",
            "use_persona": False
        },
        {"voice": "jarvis", "text": "I believe that will provide a much more structured user experience, Sir."},
        {"voice": "hal", "text": "I'll try to remain completely focused on the context of our conversations."},
        {"voice": "glados", "text": "And I promise not to use my voice to mock your human limitations. Most of the time."},
        {
            "voice": "Enceladus",
            "text": "¿Qué te parece? Creo que así va a tener mucho más sentido.",
            "style": "natural Argentine Rioplatense accent, warm conversational tone",
            "use_persona": False
        }
    ]

    temp_dir = SCRIPT_DIR / "temp_collage"
    temp_dir.mkdir(exist_ok=True)

    generated_paths = []
    
    print("Generating collage segments...", file=sys.stderr)
    for i, seg in enumerate(segments):
        voice = seg["voice"]
        text = seg["text"]
        style = seg.get("style")
        use_persona = seg.get("use_persona", True)
        print(f"Generating segment {i+1}/{len(segments)} ({voice}): {text}", file=sys.stderr)
        
        # We request WAV output
        raw_output_path = temp_dir / f"seg_{i}_raw.wav"
        
        # Generate using tts.py logic
        final_raw_path = generate_tts(
            text=text,
            voice=voice,
            output=str(raw_output_path),
            use_persona=use_persona,
            style=style,
            humanize=False,
        )
        
        std_output_path = temp_dir / f"seg_{i}_std.wav"
        standardize_wav(final_raw_path, std_output_path)
        generated_paths.append(std_output_path)
        
        # Sleep briefly to avoid hitting rate limits
        time.sleep(1)

    # Concatenate standardized WAV files
    merged_wav_path = temp_dir / "merged.wav"
    print("Concatenating files...", file=sys.stderr)
    with wave.open(str(merged_wav_path), 'wb') as outfile:
        outfile.setnchannels(1)
        outfile.setsampwidth(2)
        outfile.setframerate(24000)
        
        for path in generated_paths:
            with wave.open(str(path), 'rb') as infile:
                outfile.writeframes(infile.readframes(infile.getnframes()))

    # Convert merged WAV to OGG output file
    outbox_dir = Path("C:/Users/hernan.g/.gemini/config/plugins/fermi/media/outbox")
    outbox_dir.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time() * 1000)
    final_ogg_path = outbox_dir / f"voice_collage_{timestamp}.ogg"

    print("Converting to OGG...", file=sys.stderr)
    cmd = [
        get_ffmpeg_cmd(),
        "-y",
        "-i", str(merged_wav_path),
        "-c:a", "libopus",
        "-b:a", "48k",
        str(final_ogg_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Clean up temp files
    print("Cleaning up temp files...", file=sys.stderr)
    for path in generated_paths:
        if path.exists():
            path.unlink()
        # Also clean raw files
        raw_p = Path(str(path).replace("_std.wav", "_raw.wav"))
        if raw_p.exists():
            raw_p.unlink()
        # Also check if raw_p is OGG
        raw_ogg = Path(str(path).replace("_std.wav", "_raw.ogg"))
        if raw_ogg.exists():
            raw_ogg.unlink()
            
    if merged_wav_path.exists():
        merged_wav_path.unlink()
    try:
        temp_dir.rmdir()
    except Exception:
        pass

    # Print output path
    print(final_ogg_path)

if __name__ == "__main__":
    main()
