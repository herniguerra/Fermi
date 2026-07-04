# Memory — Learned Facts & Running Context

*Last compacted: 2026-07-03*

## Environment

- **Workstation OS**: Windows
- **Dev root**: `D:\dev\`
- **Projects tracker**: `D:\dev\Projects\` (git-tracked, syncs SUMMARY.md to Google Drive)
- **Pipeline root**: `D:\Many-Worlds\pipeline\`
- **Antigravity config**: `C:\Users\hernan.g\.gemini\config\`
- **Fermi plugin**: `C:\Users\hernan.g\.gemini\config\plugins\fermi\` → symlinked to `D:\dev\Fermi\`

## Recent Context

### 2026-07-03
- Built Fermi's Telegram relay — working end-to-end with 5s polling via subagent
- Set up email + calendar scanning for `hernan.g@many-worlds.com` with OAuth (Google Workspace)
- Added `upcoming.md` schema to project tracker for time-bound events
- Renamed old Fermi project → Dharma (`D:\dev\Dharma`, github.com/herniguerra/Dharma)
- Created Fermi as a global Antigravity plugin with persona + memory system
- Hernán wants formality/casualness to be fluid and context-driven, not pinned to platform

### 2026-07-01–02
- Built 360 turntable video script for NDN (Así Somos) published rigs in Maya
- Playblast with burn-in bar, MW logo, per-asset labels, finger/eyebrow control hiding
- Generated character figurines (reporters, photographers, fans) with Gemini Flash + rembg

### 2026-06-28–29
- Fixed missing `vehicle_chassis_01` mGear component (dropped between addon versions 0.1.10 → 0.1.12)
- Fixed AYON path override bug (`C:\projects_local` → `D:\Many-Worlds\pipeline\projects`)
- Created Maya dice generator script (superellipsoid with boolean pip engravings)
- Copied mGear rigging custom steps from santi to flor, momi, garabal

### 2026-06-26
- Built NDN board game SVG — spaces, inner ring, colored noodle-bridge tunnels
- Iterative design with ~35 rounds of feedback

## Lessons

- Keep AYON addon updates careful — files can silently drop between versions
- Hernán iterates fast — be ready for 30+ rounds of real-time feedback on visual work
- When playblasting in Maya, check `ctl_vis_on_playback` attribute on multiple possible nodes (rig root, character node, etc.)
