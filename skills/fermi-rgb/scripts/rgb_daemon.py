"""
Fermi RGB Daemon
================
Watches a state file and drives OpenRGB to reflect Fermi's current state.
Uses the openrgb-python library when an OpenRGB server is running (recommended,
runs in milliseconds and supports DRAM + Motherboard when run as Administrator).
Falls back to OpenRGB.exe CLI mode (slower, GPU + Keyboard only) if the server is offline.

States:
  - idle:     Breathing (GPU, Keyboard, DRAM, Motherboard) in faint purple
  - thinking: Pulse (GPU, DRAM, Motherboard) in amber, wave (Keyboard) in gold
  - listening: Direct (GPU, DRAM, Motherboard) in blue, static (Keyboard) in blue
  - speaking: White breathing/streaming
  - success:  Green flash then back to idle
  - error:    Red flash then back to idle
  - offline:  All off

Usage:
  python rgb_daemon.py

State file: C:/Users/hernan.g/.gemini/config/plugins/fermi/media/rgb_state.txt
"""

import subprocess
import time
import os
import sys
from pathlib import Path
from openrgb import OpenRGBClient
from openrgb.utils import DeviceType, RGBColor

# Config
OPENRGB = r"C:\Program Files\OpenRGB\OpenRGB.exe"
STATE_FILE = Path(r"C:\Users\hernan.g\.gemini\config\plugins\fermi\media\rgb_state.txt")
LOG_FILE = Path(r"C:\Users\hernan.g\.gemini\config\plugins\fermi\media\rgb_daemon.log")

# Device indices for CLI fallback (from --list-devices)
GPU = 0   # MSI RTX 4090 Gaming X Trio
KBD = 1   # VSG Mintaka

# Color palette (hex RGB)
COLORS = {
    "purple_faint":  "1A0A2E",
    "purple":        "6B2FA0",
    "amber":         "FFB300",
    "gold":          "FFC107",
    "green":         "00E676",
    "red":           "FF1744",
    "white":         "FFFFFF",
    "white_dim":     "808080",
    "off":           "000000",
}


def log(msg: str):
    """Log to file and stdout."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def run_openrgb(*args):
    """Run OpenRGB with given arguments (CLI Fallback)."""
    cmd = [OPENRGB] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        if result.returncode != 0 and result.stderr:
            log(f"  OpenRGB CLI stderr: {result.stderr.strip()}")
        return result
    except subprocess.TimeoutExpired:
        log("  OpenRGB CLI timed out")
        return None
    except Exception as e:
        log(f"  OpenRGB CLI error: {e}")
        return None


def read_state() -> str:
    """Read current state from file."""
    try:
        if STATE_FILE.exists():
            return STATE_FILE.read_text(encoding="utf-8").strip().lower()
    except Exception:
        pass
    return "idle"


def write_state(state: str):
    """Write state to file."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(state, encoding="utf-8")
    except Exception as e:
        log(f"Error writing state file: {e}")


class RGBManager:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.last_connect_attempt = 0

    def try_connect(self) -> bool:
        now = time.time()
        if now - self.last_connect_attempt < 10:
            return False  # Limit connection attempts to once per 10 seconds
        self.last_connect_attempt = now

        try:
            log("Attempting to connect to OpenRGB SDK server (127.0.0.1:6742)...")
            self.client = OpenRGBClient(address="127.0.0.1", port=6742, name="Fermi Daemon")
            self.is_connected = True
            log("Successfully connected to OpenRGB SDK server!")
            log("Detected devices:")
            for i, dev in enumerate(self.client.devices):
                log(f"  [{i}] {dev.name} (Type: {dev.type.name})")
            return True
        except Exception as e:
            log(f"Could not connect to OpenRGB server (falling back to CLI): {e}")
            self.client = None
            self.is_connected = False
            return False

    def check_connection(self) -> bool:
        if not self.is_connected or not self.client:
            return self.try_connect()

        try:
            # Quick check if client connection is still alive
            _ = self.client.protocol_version
            return True
        except Exception:
            log("Connection to OpenRGB server lost.")
            self.client = None
            self.is_connected = False
            return self.try_connect()

    def set_device_color_mode(self, dev, mode_name: str, color_hex: str):
        try:
            # Find matching mode (case-insensitive)
            mode_to_set = None
            for m in dev.modes:
                if m.name.lower() == mode_name.lower():
                    mode_to_set = m
                    break

            # Fallback if preferred mode not supported by device
            if not mode_to_set:
                fallbacks = ["direct", "static", "breathing", "solid", "color cycle"]
                for fb in fallbacks:
                    for m in dev.modes:
                        if m.name.lower() == fb:
                            mode_to_set = m
                            break
                    if mode_to_set:
                        break

            if mode_to_set:
                dev.set_mode(mode_to_set.name)
                # Some modes don't support color; only set color if mode supports it
                color = RGBColor.fromHEX(color_hex)
                dev.set_color(color)
            else:
                # Direct control fallback
                color = RGBColor.fromHEX(color_hex)
                dev.set_color(color)

            dev.show()
        except Exception as e:
            log(f"    Failed to set device {dev.name}: {e}")

    def apply_sdk_state(self, state: str):
        if state in ["offline", "off"]:
            for dev in self.client.devices:
                try:
                    dev.off()
                except Exception:
                    try:
                        dev.set_color(RGBColor(0, 0, 0))
                    except Exception:
                        pass
            return

        for dev in self.client.devices:
            target_mode = "Direct"
            target_color_hex = COLORS["off"]

            if state == "idle":
                target_color_hex = COLORS["purple_faint"]
                if dev.type == DeviceType.GPU:
                    target_mode = "Static"  # Changed from Breathing to keep GPU lit
                elif dev.type == DeviceType.KEYBOARD:
                    target_mode = "Breathing"
                elif dev.type == DeviceType.DRAM:
                    target_mode = "Breathing"
                else:
                    target_mode = "Static"

            elif state == "thinking":
                if dev.type == DeviceType.GPU:
                    target_mode = "Static"  # Changed from Flashing to keep GPU lit
                    target_color_hex = COLORS["amber"]
                elif dev.type == DeviceType.KEYBOARD:
                    target_mode = "Spectrum cycle"
                    target_color_hex = COLORS["gold"]
                elif dev.type == DeviceType.DRAM:
                    target_mode = "Static"
                    target_color_hex = COLORS["amber"]
                else:
                    target_mode = "Static"
                    target_color_hex = COLORS["gold"]

            elif state == "listening":
                target_color_hex = "2196F3"  # Soft blue
                if dev.type == DeviceType.KEYBOARD:
                    target_mode = "Static"
                else:
                    target_mode = "Direct"

            elif state == "speaking":
                if dev.type == DeviceType.GPU:
                    target_mode = "Static"  # Changed from Streaming to keep GPU lit
                    target_color_hex = COLORS["white"]
                elif dev.type == DeviceType.KEYBOARD:
                    target_mode = "Breathing"
                    target_color_hex = COLORS["white_dim"]
                else:
                    target_mode = "Static"
                    target_color_hex = COLORS["white_dim"]

            elif state == "success":
                target_color_hex = COLORS["green"]
                target_mode = "Direct"

            elif state == "error":
                target_color_hex = COLORS["red"]
                target_mode = "Direct"

            self.set_device_color_mode(dev, target_mode, target_color_hex)

    def apply_cli_state(self, state: str):
        log("  Falling back to CLI control (Slow)...")
        
        # Determine settings for GPU and Keyboard separately
        gpu_mode = "Static"
        gpu_color = COLORS["off"]
        kbd_mode = "Static"
        kbd_color = COLORS["off"]
        
        if state == "idle":
            gpu_mode = "Static"
            gpu_color = COLORS["purple_faint"]
            kbd_mode = "Breathing"
            kbd_color = COLORS["purple_faint"]
        elif state == "thinking":
            gpu_mode = "Static"
            gpu_color = COLORS["amber"]
            kbd_mode = "Spectrum cycle"
            kbd_color = COLORS["gold"]
        elif state == "listening":
            gpu_mode = "Direct"
            gpu_color = "2196F3"
            kbd_mode = "Static"
            kbd_color = "2196F3"
        elif state == "speaking":
            gpu_mode = "Static"
            gpu_color = COLORS["white"]
            kbd_mode = "Breathing"
            kbd_color = COLORS["white_dim"]
        elif state == "success":
            gpu_mode = "Direct"
            gpu_color = COLORS["green"]
            kbd_mode = "Static"
            kbd_color = COLORS["green"]
        elif state == "error":
            gpu_mode = "Direct"
            gpu_color = COLORS["red"]
            kbd_mode = "Static"
            kbd_color = COLORS["red"]
        elif state in ["offline", "off"]:
            gpu_mode = "Off"
            kbd_mode = "Off"

        # Apply settings individually to avoid parameter issues
        log(f"  CLI setting GPU to Mode={gpu_mode}, Color={gpu_color}")
        if gpu_mode == "Off":
            run_openrgb("-d", str(GPU), "-m", "Off")
        else:
            run_openrgb("-d", str(GPU), "-m", gpu_mode, "-c", gpu_color)

        log(f"  CLI setting Keyboard to Mode={kbd_mode}, Color={kbd_color}")
        if kbd_mode == "Off":
            run_openrgb("-d", str(KBD), "-m", "Off")
        else:
            run_openrgb("-d", str(KBD), "-m", kbd_mode, "-c", kbd_color)

    def apply_state(self, state: str):
        state = state.strip().lower()
        if self.check_connection():
            try:
                self.apply_sdk_state(state)
                log(f"State applied via SDK: {state}")
            except Exception as e:
                log(f"Error applying SDK state (falling back to CLI): {e}")
                self.apply_cli_state(state)
        else:
            self.apply_cli_state(state)

        # If success or error, wait 2s and revert state file to idle
        if state in ["success", "error"]:
            time.sleep(2)
            write_state("idle")


def main():
    log("=" * 50)
    log("Fermi RGB Daemon starting")
    log(f"  OpenRGB CLI: {OPENRGB}")
    log(f"  State file: {STATE_FILE}")
    log("=" * 50)

    # Verify OpenRGB exists
    if not Path(OPENRGB).exists():
        log(f"WARNING: OpenRGB not found at {OPENRGB}. CLI fallback will not work.")

    # Initialize state file if missing
    if not STATE_FILE.exists():
        write_state("idle")

    manager = RGBManager()

    # Apply initial state
    current_state = read_state()
    log(f"Initial state: {current_state}")
    manager.apply_state(current_state)

    # Watch loop
    last_state = current_state
    last_mtime = STATE_FILE.stat().st_mtime if STATE_FILE.exists() else 0

    log("Watching for state changes...")

    while True:
        try:
            if STATE_FILE.exists():
                mtime = STATE_FILE.stat().st_mtime
                if mtime != last_mtime:
                    new_state = read_state()
                    if new_state != last_state:
                        log(f"State change: {last_state} -> {new_state}")
                        manager.apply_state(new_state)
                        last_state = new_state
                    last_mtime = mtime

            time.sleep(0.5)  # Poll every 500ms

        except KeyboardInterrupt:
            log("Shutting down...")
            if manager.is_connected:
                for dev in manager.client.devices:
                    try:
                        dev.off()
                    except Exception:
                        pass
            else:
                run_openrgb("-d", str(GPU), "-m", "Off", "-d", str(KBD), "-m", "Off")
            break
        except Exception as e:
            log(f"Error in watch loop: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
