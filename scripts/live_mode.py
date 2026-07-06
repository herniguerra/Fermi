import asyncio
import os
import sys
import msvcrt
import pyaudio
import traceback
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Constants
MODEL = "gemini-3.1-flash-live-preview"
AUDIO_IN_RATE = 16000
AUDIO_OUT_RATE = 24000
CHUNK_SIZE = 2048
USE_ECHO_GATE = True  # Mutes mic while model is speaking to prevent feedback loops
VOICE = "Puck"  # Supported Live API voices: Enceladus, Aoede, Charon, Fenrir, Kore, Puck

MEMORY_DIR = r"D:\dev\Fermi\memory"
FILES_TO_LOAD = ["USER.md", "MEMORY.md", "BELIEFS.md", "TODAY.md"]

def build_system_instruction():
    instruction = "You are Fermi, Hernán's AI assistant. You are currently in a real-time LIVE VOICE conversation.\n\n"
    for filename in FILES_TO_LOAD:
        filepath = os.path.join(MEMORY_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                instruction += f"\n--- {filename} ---\n"
                instruction += f.read() + "\n"
    
    instruction += "\nKeep your responses conversational and natural for voice. Do not output markdown, just speak clearly."
    return instruction

async def audio_input_task(session, p, input_queue, is_muted, last_audio_time):
    def callback(in_data, frame_count, time_info, status):
        # Determine if echo gate should mute the mic
        gating = False
        if USE_ECHO_GATE and (time.time() - last_audio_time[0] < 0.5):
            gating = True
            
        # If muted or echo gate is active, send silence (zeros)
        if not is_muted[0] and not gating:
            input_queue.put_nowait(in_data)
        else:
            input_queue.put_nowait(b'\x00' * len(in_data))
        return (None, pyaudio.paContinue)

    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=AUDIO_IN_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        stream_callback=callback
    )
    
    stream.start_stream()
    try:
        while True:
            data = await input_queue.get()
            await session.send_realtime_input(audio={"data": data, "mime_type": "audio/pcm"})
            await asyncio.sleep(0.001)
    except asyncio.CancelledError:
        pass
    finally:
        stream.stop_stream()
        stream.close()

async def audio_output_task(session, p, last_audio_time):
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=AUDIO_OUT_RATE,
        output=True,
        frames_per_buffer=CHUNK_SIZE
    )
    
    stream.start_stream()
    try:
        while True:
            async for response in session.receive():
                server_content = response.server_content
                if server_content is not None:
                    model_turn = server_content.model_turn
                    if model_turn is not None:
                        for part in model_turn.parts:
                            if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                                audio_bytes = part.inline_data.data
                                # Run blocking write in a separate thread so it doesn't freeze the event loop
                                await asyncio.to_thread(stream.write, audio_bytes)
                                # Update timestamp after playing to keep gate closed
                                last_audio_time[0] = time.time()
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"\n[Error receiving audio] {e}")
        traceback.print_exc()
    finally:
        stream.stop_stream()
        stream.close()

async def keyboard_listener(is_muted):
    print("\n" + "="*50)
    print("FERMI LIVE MODE")
    print("Press [SPACEBAR] to toggle mute (currently MUTED by default)")
    print("Press [q] or [ESC] to quit.")
    print("="*50 + "\n")
    
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ': # Spacebar
                is_muted[0] = not is_muted[0]
                status = "MUTED" if is_muted[0] else "LISTENING..."
                print(f"\rMicrophone: {status}".ljust(40), end="", flush=True)
            elif key in [b'q', b'Q', b'\x1b']: # Q or ESC
                print("\n\nDisconnecting...")
                # Cancel the event loop tasks
                for task in asyncio.all_tasks():
                    if task is not asyncio.current_task():
                        task.cancel()
                break
        await asyncio.sleep(0.05)

async def main():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client(api_key=api_key)
    
    sys_instruction = build_system_instruction()
    
    # Live API Config
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=VOICE
                )
            )
        ),
        system_instruction=types.Content(parts=[types.Part.from_text(text=sys_instruction)])
    )
    
    p = pyaudio.PyAudio()
    input_queue = asyncio.Queue()
    is_muted = [True]  # Use a list so it can be mutated by reference
    last_audio_time = [0.0] # Use a list for reference mutation
    
    print("Connecting to Gemini Live API...")
    
    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Connected! Starting audio streams...")
            
            # Start tasks
            tasks = [
                asyncio.create_task(audio_input_task(session, p, input_queue, is_muted, last_audio_time)),
                asyncio.create_task(audio_output_task(session, p, last_audio_time)),
                asyncio.create_task(keyboard_listener(is_muted))
            ]
            
            await asyncio.gather(*tasks)
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Connection Error: {e}")
        traceback.print_exc()
    finally:
        p.terminate()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited.")
