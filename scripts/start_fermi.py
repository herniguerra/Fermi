import subprocess
import sys
import os
import time
import signal
import threading
import json
from pathlib import Path

# ANSI colors for nice logging
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Configurations
SERVICES = {
    "Gateway": {
        "command": [
            sys.executable,
            "-u",
            r"C:\Users\hernan.g\.gemini\config\plugins\fermi\skills\telegram-relay\scripts\bot.py"
        ],
        "cwd": r"C:\Users\hernan.g\.gemini\config\plugins\fermi\skills\telegram-relay\scripts",
        "color": CYAN,
    },
    "Tunnel": {
        "command": [
            r"D:\dev\Fermi\scripts\cloudflared.exe",
            "tunnel",
            "--url",
            "http://localhost:8000"
        ],
        "cwd": r"D:\dev\Fermi",
        "color": YELLOW,
    },
    "FishSpeech": {
        "command": [
            r"D:\dev\Fermi\fish_speech\venv\Scripts\python.exe",
            "-u",
            r"D:\dev\Fermi\fish_speech\fish_speech_server.py"
        ],
        "cwd": r"D:\dev\Fermi\fish_speech",
        "color": GREEN,
    }
}

active_processes = {}
shutdown_event = threading.Event()

def log(service_name, color, text):
    lines = text.strip().splitlines()
    for line in lines:
        print(f"{color}[{service_name}]{RESET} {line}", flush=True)

def update_gateway_config(url):
    config_path = r"C:\Users\hernan.g\.gemini\config\plugins\fermi\skills\telegram-relay\scripts\config.json"
    try:
        if not url.endswith("/app/"):
            url = url.rstrip("/") + "/app/"
            
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        old_url = config.get("call_url")
        if old_url != url:
            config["call_url"] = url
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            print(f"{CYAN}[Supervisor]{RESET} Updated Gateway config call_url to: {url}")
            restart_service("Gateway")
    except Exception as e:
        print(f"{RED}[Supervisor Error]{RESET} Failed to update Gateway config: {e}")

def restart_service(name):
    if name in active_processes:
        proc = active_processes[name]
        log(name, RED, f"Forcing restart...")
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        except Exception as e:
            print(f"Error terminating {name}: {e}")
            proc.terminate()

def read_output(service_name, process, color, stream_name="stdout"):
    stream = process.stdout if stream_name == "stdout" else process.stderr
    if not stream:
        return
        
    for line in iter(stream.readline, b""):
        if shutdown_event.is_set():
            break
        try:
            decoded = line.decode("utf-8", errors="replace")
            log(service_name, color, decoded)
            
            # Watch for cloudflared URL print to update config dynamically
            if service_name == "Tunnel" and "trycloudflare.com" in decoded:
                words = decoded.split()
                for word in words:
                    if "trycloudflare.com" in word:
                        url = word.strip("|").strip()
                        if url.startswith("http"):
                            update_gateway_config(url)
        except Exception as e:
            print(f"{RED}[Supervisor Error]{RESET} Failed decoding line for {service_name}: {e}")
            
    stream.close()

def start_service(name, config):
    log(name, config["color"], f"Starting command: {' '.join(config['command'])}")
    try:
        # Use shell=True for npx on Windows
        shell = True if config["command"][0] == "npx" else False
        
        proc = subprocess.Popen(
            config["command"],
            cwd=config["cwd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            bufsize=1, # Line buffered
        )
        active_processes[name] = proc
        
        # Start stdout reader thread
        t_out = threading.Thread(
            target=read_output,
            args=(name, proc, config["color"], "stdout"),
            daemon=True
        )
        t_out.start()

        # Start stderr reader thread
        t_err = threading.Thread(
            target=read_output,
            args=(name, proc, RED, "stderr"),
            daemon=True
        )
        t_err.start()
        
    except Exception as e:
        log(name, RED, f"Failed to start service: {e}")

def monitor_services():
    while not shutdown_event.is_set():
        for name, proc in list(active_processes.items()):
            # Poll if process exited
            ret = proc.poll()
            if ret is not None:
                log(name, RED, f"Process exited unexpectedly with code {ret}")
                # Remove from active list
                del active_processes[name]
                # Restart if we are not shutting down
                if not shutdown_event.is_set():
                    log(name, RED, "Attempting restart in 5 seconds...")
                    time.sleep(5)
                    if not shutdown_event.is_set():
                        start_service(name, SERVICES[name])
        time.sleep(1)

def shutdown():
    print(f"\n{RED}[Supervisor]{RESET} Shutting down all services gracefully...")
    shutdown_event.set()
    
    # Send termination signal to all
    for name, proc in active_processes.items():
        print(f"Terminating {name} (PID {proc.pid})...")
        try:
            # On Windows, taskkill is cleaner for child process trees (e.g. npx localtunnel spawns child node processes)
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        except Exception as e:
            print(f"Error terminating {name}: {e}")
            proc.terminate()
            
    # Wait for processes to exit
    for name, proc in active_processes.items():
        try:
            proc.wait(timeout=5)
            print(f"{name} exited.")
        except subprocess.TimeoutExpired:
            print(f"Forcing kill on {name}...")
            try:
                proc.kill()
            except:
                pass
                
    print(f"{RED}[Supervisor]{RESET} Shutdown complete.")
    sys.exit(0)

def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")
            print(f"{CYAN}[Supervisor]{RESET} Loaded environment variables from D:/dev/Fermi/.env")
        except Exception as e:
            print(f"{RED}[Supervisor Error]{RESET} Failed to load .env: {e}")

def signal_handler(sig, frame):
    shutdown()

if __name__ == "__main__":
    # Setup exit signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    load_env()
    print(f"{CYAN}=== Fermi Supervisor Starting ==={RESET}")
    print("Press Ctrl+C to stop all services.")

    # Start all configured services
    for name, config in SERVICES.items():
        start_service(name, config)
        time.sleep(1) # Gap startup slightly
        
    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_services, daemon=True)
    monitor_thread.start()

    # Block main thread until exit
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()
