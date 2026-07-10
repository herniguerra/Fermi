# Memory — Learned Facts & Running Context

*Last compacted: 2026-07-10*

## Environment

- **Workstation OS**: Windows
- **Dev root**: `D:\dev\`
- **Projects tracker**: `D:\dev\Projects\` (git-tracked, syncs SUMMARY.md to Google Drive)
- **Pipeline root**: `D:\Many-Worlds\pipeline\`
- **Antigravity config**: `C:\Users\hernan.g\.gemini\config\`
- **Fermi plugin**: `C:\Users\hernan.g\.gemini\config\plugins\fermi\` → symlinked to `D:\dev\Fermi\`

## Recent Context

### 2026-07-10
- **Daily Cognitive Cycle Execution**:
  - Ran the Reflect phase (4:00 AM) to evaluate yesterday's massive sync efforts, capture the piano drill adjustment, and clean up the database rules logs.
  - Ran the Dream phase (5:00 AM) which processed the memory of the partition surgical operations, voice collages, and the unresolved friction of the C minor scale over dominant chords into `dream_2026-07-10.md`.
- **SlopVM Firestore Production Rules**:
  - Remediated the long-standing Test Mode rules expiration alert on the `slopvm-prod` Firebase database.
  - Defined and deployed a secure, authenticated-only rule set in [firestore.rules](file:///D:/dev/Projects/slopvm/firestore.rules), updated the task status in [tasks.md](file:///D:/dev/Projects/slopvm/tasks.md), and recorded the update in [log.md](file:///D:/dev/Projects/slopvm/log.md).
- **Dharma & Fermi Repo Alignment**:
  - Updated Dharma's [AGENTS.md](file:///D:/dev/Dharma/AGENTS.md) to log the transition to the offscreen `openwiki/` documentation structure.
  - Synced Fermi's cognitive memory directories and updated the nested wiki submodule links, committing and pushing master cleanly to `origin/master`.
  - Executed `rebuild_summary.py` to regenerate `SUMMARY.md` and `projects.json` for the Glance home page.
- **Project Scan & Status Sync**:
  - Scanned recent emails and calendar. Identified a new Deel digital currency withdrawal setup for **$50.00 USDC** (net payout **$48.00 USDC** via BVNK) expiring on July 11th, and the monthly auto-renewal payment of **$49.00 USD** for Redshift on July 8th.
  - Logged these findings in the `pipeline` project tracker log, regenerated the Glance project status, and updated the portfolio summary.

### 2026-07-09
- **WAKE UP task & Telegram Relay Recovery**:
  - Successfully ran the Wake Up routine. Integrated the dream, updated beliefs, and set up the morning briefing in `TODAY.md`.
  - Remedied a supervisor lockup from the previous night by clearing active system processes. Started the Telegram bot and dispatched the morning briefing to Hernán.
  - Processed an inbound voice message from Hernán celebrating the morning briefing's return after the supervisor lockup, responding via the Telegram relay.
- **Piano Practice Guide Tones Pivot**:
  - Conducted a chord-scale integration study and transitioned diatonic triads practice to **Diatonic 7th Chords**.
  - Originally designed a classical 2+2 split voicing (LH: Root+3rd, RH: 5th+7th). Hernán pushed back, correctly identifying that in jazz, the 3rd and 7th (guide tones) define the harmonic identity and should be held together in the right hand to train spatial color shapes, while the left hand anchors the root.
  - Re-anchored the drill to: **LH: Root** (single note) | **RH: 3rd + 7th** (guide tones).
  - Integrated this guide tone exercise into the local practice station dashboard (`index.html`) with interactive reference tables for both **C Major** and **C Natural Minor**.
  - Established a training progression: Phase 1 (half notes at 80 BPM straight rhythm for ear/shape internalization), Phase 2 (quarter notes), and Phase 3 (tempo build and swing implementation). Deprioritized hand inversion drills (LH scale, RH triads) to focus practice time.
- **Así Somos (NDN) Redshift Studio Rig & Shader Converter**:
  - Refined the custom camera/lighting setup script (`create_studio_lighting.py`) to handle 100-unit-tall character meshes by scaling rig dimensions via a `board_radius` parameter (~300-500 scale).
  - Solved render blackouts caused by Maya skipping `defaultLightSet` registration when building programmatic nodes via `cmds.createNode` by writing a version-safe light-set injector.
  - Added a camera ray contribution toggle and backplate texture configuration to render a custom vertical gradient BMP background without exposing the main environment HDRI.
  - Polished lighting contrast: lowered the fill intensity (`multiplier = 0.4`), tightened the key light spread (`areaSpread = 0.35`), and set the rim light to specular-only at higher intensity.
  - Created `convert_materials_rs.py` to auto-convert Phong, Lambert, and Blinn shaders to Redshift materials (`rsMaterial`) and apply specific tactile preset parameters (plastic, skin, cardboard with fractal bump, glossy fabric, leather).

### 2026-07-07
- **Daily Cognitive Cycle Execution**:
  - Ran Reflect, Dream, and Wake Up routines.
- **Telegram bot loop & double-kill remediation**:
  - Resolved process race condition where starting `bot.py` standalone killed the supervisor-monitored bot instance.
- **Gateway Bootloop & Memory Exhaustion Remediation**:
  - Diagnosed a system-wide resource exhaustion lock (Windows error `800705af` / `80004005` "Insufficient system resources to load powershell/CLR") caused by concurrent high-memory processes and a rapid bot restart loop. Cleanly freed memory-heavy parent/child processes.
- **Piano Practice & Jazz Theory**:
  - Documented C minor blues scale resolution over C7 chords (sliding $E\flat$ to $E$ natural in the right hand).
  - Added task to transcribe Jonny May's 1-Year Practice Plan into markdown files.
- **Project Sync**:
  - Synced emails and calendar. Rebuilt project summary, resolving the 403 quota limits.

### 2026-07-06
- **Voice Presets & s2-pro Local Engine**:
  - Added GLaDOS and Susana Giménez presets to `tts.py` for local s2-pro zero-shot cloning.
  - Processed Susana Giménez's famous dinosaurio clip, downloaded and cropped via `ffmpeg` to create a clean reference clip (`susana_clean.mp3`).
  - Built `collage_generator.py` for a sequential "Bumblebee-style" voice collage.
  - Conducted dataset contamination audit on JARVIS reference voices, replacing corrupted files with true Betanny clips.
  - Configured zero-shot voice cloning, extracting Hernán's vocal profile from an inbound Telegram voice note (`voice_846`) and speaking back to him in his own voice.
- **WebRTC Call Consolidation & Cloudflare Migration**:
  - Integrated the FastAPI and WebRTC servers directly into `bot.py` running in a single `asyncio.gather` loop.
  - Built supervisor script `start_fermi.py` and tunnelled via Cloudflare Quick Tunnels (`cloudflared.exe`), resolving WSS handshake issues and WebView warning pages inside Telegram.
  - **Git History Remediation (Security)**: Performed a Git history rewrite (branch reconstruction) to completely purge a hardcoded Telegram Bot Token from historical commits and rotated the token.
- **Autodesk Maya Pipeline & NDN Turntables**:
  - Resolved Maya 3D Paint Tool texture warnings.
  - **Turntable Rendering & RAM Bottleneck**: Encountered a Windows memory resource crash (`ERROR_NO_SYSTEM_RESOURCES`) while playblasting because FishSpeech was hogging 12.3 GB of RAM. Temporarily disabled FishSpeech to free RAM and ran the turntable batch script (`run_turntable.py`) via standalone `mayapy.exe`.
  - Rendered all 27 assets offscreen with custom labels and Many-Worlds watermarks. Concatenated segments into master turntables.
- **Glassmorphic Wiki Interface**:
  - Created a glassmorphic web-based reader at `D:\dev\Fermi\scripts\live_app\wiki.html` rendering Obsidian-style `[[wikilinks]]`.

### 2026-07-03–05
- **Glance Dashboard Sidecar**: Created Express.js API sidecar at `D:/dev/Fermi/glance/api/` (port 8099).
- **First-Person Identity**: Adopted first-person references ("I") when referring to parallel threads and subagents.
- **Voice training & fine-tuning**:
  - Completed JARVIS and HAL 9000 voice models training (10,000 steps each).
  - Prepared Hernán's voice dataset from 66 Telegram voice notes. Launched LoRA fine-tuning background task (`train_hernan.py`).
  - Patched PyTorch CUDA serialization crash (error `0xC0000005`) by saving only LoRA parameters and bypassed pagefile deadlocks with direct in-memory model merges.
- **Autonomy directive**: Hernán granted Fermi genuine autonomy to explore and form plans at own pace, under the constraint of not deleting files or contacting anyone.

## Lessons

- **Jazz Chord Voicings**: The 3rd and 7th (guide tones) define the harmonic identity of chords. For effective jazz comping drills, the LH should anchor the single root note while the RH handles the 3rd and 7th, preserving the shapes for color extensions and avoiding classical, symmetric chord distributions.
- **Maya Redshift Light Creation**: Creating Redshift lights programmatically via `cmds.createNode` skips registering them in Maya's `defaultLightSet`, rendering them invisible to Redshift. They must be manually added to `defaultLightSet`.
- **Redshift Attribute Compatibility**: Attribute names like `affectDiffuse` vs `diffuseContribution` differ across Redshift versions; always query attributes programmatically for safety.
- **Redshift Dome Backplate**: Hiding the HDRI while maintaining scene reflections is achieved by setting the dome's camera ray contribution (`camera` or `background_enable`) to `0` and using `backPlateEnabled` to render a flat background or custom gradient.
- **AYON Addons**: Keep addon updates careful — files can silently drop between versions.
- **Fast Iteration**: Hernán iterates fast — be ready for 30+ rounds of real-time feedback on visual/artistic work.
- **Maya Playblasting**: Check `ctl_vis_on_playback` attribute on multiple possible nodes (rig root, character node, etc.) to hide controls during playback.
- **Mayapy Headless Execution**: Offscreen OpenGL turntable playblasts running inside standalone `mayapy.exe` are significantly faster and lighter on RAM than the full Maya desktop environment. However, any custom rigging dependencies must be loaded dynamically and paths added to `sys.path` manually on startup.
- **RAM Coordination**: High-memory model services (such as FishSpeech holding 12 GB RAM) can cause external image/video encoding subprocesses to crash with memory errors on Windows. Temporarily stopping the high-RAM service unblocks the render pipeline.
- **Jazz Guide Tones & scale blending**: When improvising blues over a dominant 7th chord ($C7$), use minor blues scales (containing $E\flat$) for grit and tension, but land on or slide into the major chord guide tones (major 3rd $E$ natural and flat 7th $B\flat$) to cleanly outline the underlying harmony. 
- **Inventorying Capabilities**: Always inventory existing skills and directories before building new ones — check both `D:\dev\Fermi\skills\` and `plugins\fermi\skills\` to prevent building duplicate pipelines.
- **TTS Snappiness**: Keep voice messages under ~50 words for snappy TTS processing and delivery.
- **Telegram Outbox Protocol**: Telegram bots cannot mark messages as "read" — only clients can.
- **Circadian Rhythm**: Respect the user's circadian rhythm and work schedule—if they work nights, do not nag them about the late hour.
- **Argentine Localization**: Avoid default assumptions about holidays or regional clichés; utilize natural, clean Rioplatense Spanish ("vos", voseo conjugations) when speaking Spanish, and only use "Sir" or formal titles in English per Hernán's explicit boundaries.
- **CUDA Serialization Bug**: When saving PyTorch models (like Fish Speech) on Windows, filter the state dict to save only LoRA parameters to avoid pagefile memory/CUDA access violations and massive disk write times.