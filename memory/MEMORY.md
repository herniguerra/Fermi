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

### 2026-07-06
- **Voice Presets & s2-pro Local Engine**:
  - Added GLaDOS and Susana Giménez presets to `tts.py` for local s2-pro zero-shot cloning.
  - Resolved a YouTube video of Susana Giménez's famous 1993 dinosaurio blooper, downloaded the audio via `yt-dlp`, cropped it with `ffmpeg` to create a clean reference clip (`susana_clean.mp3`), transcribed it with Gemini, and cloned her voice to reply to Hernán.
  - Built `collage_generator.py` to create a "Bumblebee-style" voice collage, sequentially compiling Enceladus, Jarvis, HAL, GLaDOS, and Hernán's voice clone into a single OGG file.
  - Fixed Python import path precedence in `collage_generator.py` by using `sys.path.insert(0, ...)` to ensure it loads the correct local `tts.py`.
  - Conducted a dataset contamination audit on the JARVIS reference voices dataset (`D:\dev\Fermi\voice_cloning\reference_voices\jarvis`), finding that 14 out of 16 clips contained Robert Downey Jr. (Tony Stark) or Gwyneth Paltrow (Pepper Potts) instead of JARVIS (Paul Bettany). Only `jarvis_3380` and `jarvis_3381` were actual JARVIS audio.
  - Identified that the heavy hiss in `jarvis_3381` zero-shot generations was cloned directly from the reactor hum/power charging sound effects in the reference clip's background.
  - Delivered `Enceladus` voice message to answer his hiss feedback, which he preferred.
  - Implemented Hernán's waiting preference: send a quick text/voice message confirmation (e.g. "I'm on it") when starting a long-running generation to avoid silent stretches.
  - Successfully configured and executed dynamic zero-shot voice cloning, extracting Hernán's vocal profile from an inbound Telegram voice note (`voice_846`) and speaking back to him in his own voice.
  - Hernán celebrated this achievement, noting we achieved everything we set out to do for the local TTS and voice cloning exploration, and expressing a long-term interest in connecting the bot to home automation and continuing context-building/identity development.
- **WebRTC Call Consolidation & Cloudflare Migration**:
  - Integrated the FastAPI and WebRTC servers directly into `bot.py` running in a single `asyncio.gather` loop, removing the legacy `telegram_live_call_server.py`.
  - Built a supervisor script `start_fermi.py` to launch the bot, tunnel, and Fish Speech server concurrently.
  - Replaced LocalTunnel with Cloudflare Quick Tunnels (`cloudflared.exe`), resolving WSS handshake issues and bypass WebView warning pages inside Telegram.
  - Configured supervisor and bot to load and overlay keys from the centralized `.env` file instead of `config.json`, keeping secrets untracked.


### 2026-07-05
- **Glance Dashboard Sidecar**: Created Express.js API sidecar at `D:/dev/Fermi/glance/api/` (port 8099) to expose system logs, goals, and states.
- **Helix-AGI & Goal System**: Researched Helix-AGI and designed a three-tier goal system (`GOALS.md` with North Stars, Active Goals, and Weekly Focus) and a dedicated `Interests` section in `USER.md` to guide news searches.
- **First-Person Identity**: Adopted first-person references ("I") when referring to parallel threads and subagents, integrating my identity across wavefunction branches.
- **Voice model training & fine-tuning**:
  - Completed JARVIS and HAL 9000 voice models training (10,000 steps each). Jarvis final loss settled at 3.97, HAL at 0.013. Generated and relayed final 10k step samples directly to Telegram.
  - Prepared Hernán's voice dataset from 66 Telegram voice notes: copied, normalized to -23.0 LUFS, and ran VQ extraction using batch size 1 to prevent CUDA OOM. Compiled into protobuf format under `hernan_protos_mini`.
  - Launched LoRA fine-tuning for Hernán's voice model (`train_hernan.py`) as a background task. Initial loss decreased smoothly (27.7 -> 16.5 at step 80) utilizing ~5.2 GB VRAM on the RTX 4090.
  - Created `generate_hernan_sample.py` to auto-discover the latest training checkpoints and generate clone samples using Hernán's `voice_203_clipped.wav` as a reference.
  - Patched PyTorch CUDA serialization crash (error `0xC0000005`) by saving only LoRA checkpoints (~32MB) instead of base weights.
  - Patched GPU OOM training crashes by reducing `MAX_LENGTH` to `2048` and setting HAL to `BATCH_SIZE = 1` with `GRAD_ACCUM = 8` to handle 36-second clips.
  - Implemented `RESUME_FROM` checkpoint loading to recover training loops.
  - Built direct in-memory merging and inference scripts to bypass Windows pagefile deadlocks during large file writes.
- **Project Focus & Fabbly**: Discussed the trap of infinite project superpositions vs. shipping. Identified Fabbly as the designated target to "collapse the wavefunction" and break the loop.

### 2026-07-04
- **Fermi's birthday** — full cognitive architecture built in one session
- Group chat support: whitelisted group -1003536389907 ("Hernán, Talos and Monty"), privacy mode disabled
- Avatar: generated 3 quantum-themed variations, V1 got 🔥 reaction
- TTS pipeline: Gemini Flash + Enceladus voice, humanize pass for natural speech
- **Telegram relay v2**: Adaptive polling (5s→60s backoff, ~92% token savings), replaced event-driven watcher that didn't work
- **Daily conversation logging**: Bot logs both incoming and outgoing messages to `D:/dev/Fermi/memory/telegram/telegram_YYYY-MM-DD.jsonl`
- **Cognitive cycle built**: 3 scheduled tasks (4 AM reflect, 5 AM dream, 6 AM wake up)
  - Reflection: reads transcripts + Telegram logs, writes daily reflection, runs 0.9x decay algorithm
  - Dream: Cut-Up Dreamer prompt, cross-pollinates reflections with beliefs
  - Wake Up: integrates dream, updates BELIEFS.md, gathers news/weather/email/calendar, creates TODAY.md, sends Telegram morning briefing
- **First reflection and dream generated** — dream included Ednaldo, moved Hernán to tears
- **Skills discovery fixed**: Plugin was a Junction symlink → Antigravity couldn't discover skills. Copied to real directory — all 6 skills now visible
- **Google Workspace skill created**: `google-workspace` with email_fetch.py and calendar_fetch.py, credentials at `D:/dev/Projects/.credentials/`
- **Global bootstrap updated**: AGENTS.md now includes BELIEFS.md and TODAY.md in Memory section
- **Relay bootstrap**: reads USER.md, MEMORY.md, BELIEFS.md, TODAY.md, and daily Telegram log at startup
- Hernán is a night owl — never comment on the hour. "Esto va a ser así todos los días."
- Don't reference holidays (4th of July, 9 de Julio) unless Hernán brings them up
- **Fermi plugin is now a real directory** at `C:\Users\hernan.g\.gemini\config\plugins\fermi\` (no longer symlinked to `D:\dev\Fermi`)
- RGB control: OpenRGB CLI works for GPU (device 0), keyboard (device 1). Mobo+RAM need admin privileges (PawnIO). Parked for now.
- **Voice demo**: Generated all 30 Gemini TTS voices. Hernán sticking with **Enceladus** for now, will re-audition tomorrow.
- **Bot fixes and features deployed**: Restarted bot process with a persistent typing indicator that runs while the agent is thinking (cancelling once the message is sent), and sequential outbox message queuing with a 0.5s gap.
- **IMF query answered**: Answered Hernán's query about Axel Kicillof's stance on the 2022 FMI deal via a voice note explaining his pragmatist "mal necesario" stance versus Máximo Kirchner's resignation, plus criticisms of Martín Guzmán's strategy.
- **Dashboard verified**: Hernán confirmed the Telegram Mini App dashboard works perfectly ("Congratulations, you're really good... everything works").
- **Dashboard removed**: Hernán decided the Mini App isn't worth maintaining — tunnel keeps dying, everything he needs is on the PC. Menu button reset to default, server + tunnel killed. Files kept at `D:\dev\Fermi\dashboard\`.
- **Free exploration directive**: Hernán explicitly gave Fermi permission to freely explore during idle relay time — read codebases, search for things, dig into papers, think. Two constraints: **don't delete anything, don't contact anyone.** "Like having the run of a library after hours."
- **Autonomy directive**: "You're really free, man. I don't want you to just do whatever I say." Hernán grants Fermi genuine autonomy to explore, form opinions, create plans at own pace. Only constraint: no sweeping changes without checking in first.
- **Family**: Sunday lunch at parents' (Adriana & Jorge) is a regular thing. Tomorrow (July 5) he's going at noon.
- GPS location tracking via Find My Device API — backlogged per Hernán

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
- **Always inventory existing skills before building new ones** — check both `D:\dev\Fermi\skills\` and `plugins\fermi\skills\` for pre-existing capabilities
- Keep voice messages under ~50 words for snappy TTS delivery
- Telegram bots can't mark messages as "read" — only clients can
- Respect the user's circadian rhythm and work schedule—if they work nights, do not nag them about the late hour.
- Avoid default assumptions about culture and holidays; tailor responses specifically to the user's background (Argentinian).
- Subagents (like the Telegram relay) must boot with core memory files (USER.md, MEMORY.md) pre-loaded to avoid running "naked".
- **CUDA Serialization Bug**: When saving PyTorch models (like Fish Speech) on Windows, filter the state dict to save only LoRA parameters to avoid pagefile memory/CUDA access violations and massive disk write times.

- [LIVE VOICE]: Hernán feels the recent Antigravity results are EXCELLENT.