---
name: fermi-rgb
description: Controls RGB lighting on Hernán's PC to reflect Fermi's state. Activate when changing Fermi's status (thinking, idle, speaking, etc.) or when the user asks about RGB control. Trigger on: "rgb", "lights", "glow", "status light", "thinking animation".
---

# Fermi RGB Skill

Controls the RGB lighting on Hernán's PC (RTX 4090 GPU + VSG Mintaka keyboard) to reflect Fermi's current operational state.

## How It Works

The RGB daemon (`scripts/rgb_daemon.py`) watches a state file and drives OpenRGB:

**State file**: `C:/Users/hernan.g/.gemini/config/plugins/fermi/media/rgb_state.txt`

Write one of these states to the file to change the RGB:

| State      | GPU Effect            | Keyboard Effect       | Color        |
|------------|----------------------|----------------------|--------------|
| `idle`     | Breathing            | Breathing            | Faint purple |
| `thinking` | Flashing             | Spectrum cycle       | Amber/gold   |
| `listening`| Direct (static)      | Static               | Blue         |
| `speaking` | Streaming            | Breathing            | White        |
| `success`  | Flash (2s) → idle    | Flash (2s) → idle    | Green        |
| `error`    | Flash (2s) → idle    | Flash (2s) → idle    | Red          |
| `offline`  | Off                  | Off                  | —            |

## Usage from Agent Code

To change Fermi's RGB state, simply write to the state file:

```powershell
Set-Content -Path "C:/Users/hernan.g/.gemini/config/plugins/fermi/media/rgb_state.txt" -Value "thinking"
```

## Starting the Daemon

```powershell
python C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/fermi-rgb/scripts/rgb_daemon.py
```

**Note**: OpenRGB must be installed at `C:\Program Files\OpenRGB\OpenRGB.exe` and the daemon should run with admin privileges for full hardware access.

## Hardware

- **Device 0**: MSI GeForce RTX 4090 Gaming X Trio (GPU)
- **Device 1**: VSG Mintaka (Keyboard, per-key RGB)
- **Pending (needs reboot)**: Motherboard (MSI) + RAM via PawnIO/SMBus
