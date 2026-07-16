# Memory — Learned Facts & Running Context

*Last compacted: 2026-07-16*

## Environment

- **Workstation OS**: Windows
- **Dev root**: `D:\dev\`
- **Projects tracker**: `D:\dev\Projects\` (git-tracked, syncs SUMMARY.md to Google Drive)
- **Pipeline root**: `D:\Many-Worlds\pipeline\`
- **Antigravity config**: `C:\Users\hernan.g\.gemini\config\`
- **Fermi plugin**: `C:\Users\hernan.g\.gemini\config\plugins\fermi\` → symlinked to `D:\dev\Fermi\`

## Recent Context

### 2026-07-16
- **Project Scan & Sync (00:02 - 03:02 Local)**:
  - Scanned recent conversations, emails, and calendar events. Verified no new updates since the previous hour.
  - Rebuilt local summary (`SUMMARY.md` / `projects.json`) and successfully synced to Google Drive.
  - Created session-specific project scan summaries and committed all outstanding unstaged changes to git.
- **Piano (Interstellar Solo Project)**:
  - Explored custom MIDI conversion workflows for Magnus Baumgartl's (MrBromaba) *Interstellar* piano cover video.
  - Analyzed the official Musicnotes sheet music PDF (`Interstellar (Main Theme) - A Minor - MN0225967.pdf`) purchased by Hernán in 2021.
  - Discovered that direct PDF-to-MIDI data extraction is impossible due to custom font obfuscation (`/KPSHBO+Doremi`) and raw vector path representations of notes.
  - Initiated development of a lightweight Python Synthesia-to-MIDI parser using `opencv-python` and `mido` to extract performance-exact MIDI (capturing rubato and dynamic velocities) directly from the video file, bypassing sterile OMR sheet converters or heavy ML environments.

### 2026-07-15
- **Project Scan & Sync**:
  - Scanned recent Antigravity conversations, work emails, and calendar events.
  - Fetched and processed 93 emails and 1 calendar event.
  - Synced updates into respective project folders:
    - **Así Somos**: Logged music track v3 receipt and director feedback sheet updates; updated the upcoming virtual meeting with Google Meet link and added tasks (board references, LookDev doll texture, music alignment).
    - **Piano**: Logged YouTube Interstellar piano solo analysis and download of `interstellar.m4a` to `D:\dev\Piano`.
    - **Fermi**: Logged the morning Dream task run (`dream_2026-07-15.md`).
  - Rebuilt `SUMMARY.md` and `projects.json`, and synced to Google Drive successfully.
- **Así Somos / Many-Worlds Playblasts**:
  - Encoded 20 sequences of shots (0100 through 0900 including inserts) with a padded burn-in design. Swapped the transparent overlay for a 64px bottom-pad black bar to avoid obstructing character animation (processed via `encode_playblasts.ps1`).
  - Logged ongoing board design activities on the desktop (`board2.af~lock~` and `board3.af~lock~`) at 01:02, 02:02, and 03:02 Local Time.
- **Maya Credits Rig Tool Development**:
  - Programmed a custom Python utility (`credits_rig_tool.py` at `D:\Many-Worlds\pipeline\scripts\`) using pure dependency graph nodes (no MEL expressions) to animate credits text.
  - Features include: dynamic tracking (letter/word spacing), animatable stagger reveal properties (scale, vertical slide, opacity), custom center-alignment based on bounding box, and automatic normal conformance (+Z facing).
  - Expanded utility with: "Duplicate Setup" (keyframes, curves, and tangent data copying), JSON export/import (with text and group offset overrides), and "Regenerate Selected" (allowing text/font updates while preserving existing animation curves).
- **TimesFM Forecasting local setup**:
  - Installed Google's `timesfm[torch]` locally in `D:\dev\Fermi\timesfm_venv\` on the RTX 4090 workstation.
  - Adjusted synthetic baseline values to match the current 2026 reality (~1,500 ARS/USD) for accurate 90-day Peso-Dollar crawling peg projections.
  - Exported prediction data and dispatched dark-themed visualization plots to Hernán's Telegram.
- **Hourly Project Syncs**:
  - Managed hourly sync cycles up to 03:02 Local Time. Noted that automated Google Drive updates hit intermittent 403 API rate limit errors due to scheduling frequency, but local dashboard tracking (`SUMMARY.md` / `projects.json`) successfully compiled.

### 2026-07-14
- **Disney Client Feedback & Delivery**:
  - Attended Teams meeting "NDN / Apertura Look Personajes" with Julieta Fernandez (Disney) at 16:00 Local.
  - Received Alejandra Abdala's (Disney) feedback spreadsheet link: [NDN - Devolución Apertura 13 Julio](https://docs.google.com/spreadsheets/d/1tZbIlzh8a5clReTwoNUB7uki6wvztmeEKFwzWbiQ4Fw/edit?usp=sharing). Added granular subtasks in `tasks.md` addressing specific character height alignments, face details (Martín's beard, Momi's dimensions, Nico's muscles, Flor's side hair, scaling Santi), volumetric logo/title test adjustments, and 24x24 board extensions.
- **Recruitment & Infrastructure Updates**:
  - Tracked GoDaddy billing failures (Customer No. 593258558), Replit application retention notices (required action before Aug 8th), and Redshift auto-renewals.

### 2026-07-12
- **Así Somos (NDN) Redshift Shader Troubleshooting & Custom UI**:
  - Solved Redshift Standard Material crash issue where connecting float outputs directly to `.bump_input` caused rendering blackouts. Routed them using a native Maya `bump2d` node with color inputs (`MaxonNoise.outColorR` -> `bump2d.bumpValue` -> `material.bump_input`).
  - Created a live-tuning PySide2 tool (`clay_bump_controls.py` v4) to apply and adjust custom clay shader bump mappings across all 17 character materials simultaneously.
- **Procedural Camera Shake Tool**:
  - Created `camera_shake.py` using Perlin noise mathematics to bake high-fidelity translation/rotation keyframes directly onto camera parent transforms, bypassing performance-taxing expressions.

### 2026-07-11
- **MPFB2 Character Pipeline Sprint & Pivot**:
  - Explored parametric character generation via Blender's MPFB2 addon. Resolved headless background execution path issues. Restructured raw GitHub assets (259 MB) into the local `.user` extension directory to install teeth, skins, hair, and casual suits.
  - Rendered clothed setups for Santi, Nico, Flor, Momi, and Garabal.
  - Hernán rejected the procedural meshes as too generic for likenesses. Pivoted back to polishing the original high-quality hand-crafted models.

### 2026-07-10
- **SlopVM Firestore Production Rules**:
  - Remedied the test rules expiration alert on the `slopvm-prod` Firebase database by writing and deploying a secure, authenticated-only rule set in `firestore.rules`.

### 2026-07-09
- **Piano Practice Guide Tones Pivot**:
  - Transitioned practice drills to Diatonic 7th Chords (LH: Single Root, RH: 3rd + 7th guide tones) to establish proper jazz comping structures. Updated local training dashboard (`index.html`) with interactive reference sheets.

## Lessons

- **Musicnotes PDF Obfuscation**: Musicnotes sheet music PDFs protect intellectual property by using obfuscated custom fonts (e.g., `/KPSHBO+Doremi` encoding mapped to proprietary musical glyphs) and representing notes/staves as raw vector drawing coordinates (`moveto`, `lineto`). This prevents standard text parsers or basic PDF scrapers from extracting semantic musical data directly from the file.
- **Synthesia-to-MIDI Computer Vision Advantage**: For Synthesia-style piano visualizer videos, custom pixel-tracking scripts (using OpenCV and `mido` to detect note bars hitting the virtual keyboard line) provide mathematically perfect MIDI transcriptions. Unlike AI audio transcription tools, this approach is immune to errors from heavy pedaling, complex chords, or expressive tempo fluctuations (*rubato*), and captures exact performance durations and velocities.
- **Maya Normal Conformance**: Curve-to-mesh conversions (like Type/text geometries or `planarSrf` operations) often produce erratic, backward-facing normal winding. Solve this programmatically by applying `polyNormal(normalMode=2)` to conform, sampling a face normal, and reversing if the Z component is negative.
- **Maya Global Scale (Hierarchy)**: Driving scale transformations directly on individual letter geometries under spacing constraints causes scaling clumping. Instead, connect global scale attributes to the parent transform group (`letters_GRP`) to proportionally scale both letter sizes and calculated offsets.
- **FFmpeg Padding vs. Overlay**: To preserve camera framing boundaries while adding metadata overlays, use `-vf "pad=width:height+pad_h:0:0:color, drawtext=..."` to append a dedicated info strip below the video content.
- **Local Forecasting Models (VRAM)**: Google's TimesFM model runs efficiently locally in its own virtual environment on the 4090 GPU without clashing with DCC tasks if queries are cleanly isolated and synthetic baseline inputs match regional pricing levels.
- **Windows Scheduled Tasks execution**: Running Python scripts via scheduled tasks can fail with file-not-found codes if called as a bare system command inside restricted shells. Use absolute interpreter paths (e.g. `C:/Python311/python.exe`) and update scheduled actions programmatically via PowerShell `Set-ScheduledTask` to bypass Administrator password prompts.
- **Blender 5.0 Background Extensions**: Extensions are not loaded automatically when running Blender in `--background` mode without loading user preferences. Load the user preferences blend file or use `bl_ext` references to guarantee the addon registers.
- **Blender 5.0 EEVEE Engine Name**: In Blender 5.0, the EEVEE engine is referred to simply as `BLENDER_EEVEE` in scene settings, changing from `BLENDER_EEVEE_NEXT` in Blender 4.2.
- **FFmpeg Image Sequence Burn-In**: When designing burn-in filters with complex text overlays (frame counts, labels, logo images) using the `drawtext` and `overlay` filters in PowerShell scripts, use single-quoted here-strings to prevent PowerShell from incorrectly interpreting parentheses as sub-expressions.
- **Maya Redshift Noise scale**: In certain Redshift versions, global scale values on `RedshiftMaxonNoise` nodes are set via the `coord_scale_global` attribute rather than `overall_scale` or `scale`. Default units can be excessively large, requiring scale adjustments into the `50–150` range for visible mesh features on detailed character models.
- **Maya Redshift Node Type compatibility**: Redshift materials do not accept connections from float-based output attributes (such as `.outAlpha` of Maya procedural textures or file nodes) inside their `.bump_input` channels when processed through `RedshiftBumpMap`. Route them using `.outColor` attributes or leverage a native Maya `bump2d` node as a bridge.
- **Maya Playblast overrides**: Visibility discrepancies between viewport meshes and output playblasts are usually caused by shape node display overrides (`overrideEnabled`, `overrideDisplayType`, `overrideVisibility`) on referenced rigs.
- **Procedural Camera Shake (No Expressions)**: Animating camera shake by programmatically baking Python-calculated Perlin noise values onto group transforms is an excellent, lightweight alternative to runtime-computed expression scripts. It avoids expression execution overhead and makes the resulting keys fully editable in the Graph Editor.
- **Jazz Chord Voicings**: The 3rd and 7th (guide tones) define the harmonic identity of chords. For effective jazz comping drills, the LH should anchor the single root note while the RH handles the 3rd and 7th, preserving the shapes for color extensions and avoiding classical, symmetric chord distributions.
- **Maya Redshift Light Creation**: Creating Redshift lights programmatically via `cmds.createNode` skips registering them in Maya's `defaultLightSet`, rendering them invisible to Redshift. They must be manually added to `defaultLightSet`.
- **Redshift Dome Backplate**: Hiding the HDRI while maintaining scene reflections is achieved by setting the dome's camera ray contribution (`camera` or `background_enable`) to `0` and using `backPlateEnabled` to render a flat background or custom gradient.
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
- **Strict Language Matching**: Always reply in the exact language used by Hernán. Do not mix languages (e.g., replying in Spanish to an English query) as this is highly annoying and breaks usability.
- **Procedural Likeness Limitations**: Parametric model generators (like MPFB2) are excellent for quick rigging and proportions but cannot capture specific personal likenesses required for stylized character figurines. Stick to hand-crafted modeling when likeness is critical.
- **Linguistic Phase Locking**: Matching the user's exact language in every thread and voice message is necessary for alignment. Treating a secondary language as a default breaks the shared context.
- **Word-Frequency Language Classification**: Using simple accent-mark scanning to detect Spanish text fails when English messages contain accented names (e.g., "Hernán"). Comparing word-frequency count ratios provides robust language detection.
- **Port Reuse on Bot Restart**: When running a Telegram bot script in a Windows subprocess environment, prevent crashes on script restart by cleanly terminating any lock holding processes on port 8000 and utilizing the stored `.pid` references.
- **Affinity Lock-File Archaeology**: Affinity Designer creates lock files (`.af~lock~`) when documents are open. Monitoring these lock files allows detecting active design sessions via file-system checks without needing to monitor active system processes.
- **Google Drive Rate Limits**: Frequent automated synchronization of project files (such as hourly cycles) can hit Google Drive 403 API rate limits. Local file compilation (`SUMMARY.md`, `projects.json`) should be decoupled from the cloud sync step to ensure local dashboard stability.