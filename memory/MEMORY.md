# Memory — Learned Facts & Running Context

*Last compacted: 2026-07-14*

## Environment

- **Workstation OS**: Windows
- **Dev root**: `D:\dev\`
- **Projects tracker**: `D:\dev\Projects\` (git-tracked, syncs SUMMARY.md to Google Drive)
- **Pipeline root**: `D:\Many-Worlds\pipeline\`
- **Antigravity config**: `C:\Users\hernan.g\.gemini\config\`
- **Fermi plugin**: `C:\Users\hernan.g\.gemini\config\plugins\fermi\` → symlinked to `D:\dev\Fermi\`

## Recent Context

### 2026-07-14
- **Así Somos (NDN) Artwork & Playblasts grinding**:
  - Detected ongoing late-night layout design on boards `board2.af` and `board3.af` (active lock files modified around 03:00 Local).
  - Built a batch transcoder script `encode_playblasts.ps1` in PowerShell using FFmpeg to process playblast image sequences for 20 shots (0100 through 0900 including inserts). 
  - Restored stable scheduled task actions (`Reflect`, `Dream`, `WakeUp`) by writing a PowerShell script using `Set-ScheduledTask` to replace bare `python` execution with the absolute path of the Python 3.11.9 binary.
  - Managed bot port conflicts and lock files (`bot.pid` on port 8000) to ensure continuous Telegram relay operations.

### 2026-07-13
- **Disney Client Feedback & Delivery**:
  - Attended Teams meeting "NDN / Apertura Look Personajes" with Julieta Fernandez (Disney) at 16:00 Local.
  - Received Alejandra Abdala's (Disney) feedback spreadsheet link: [NDN - Devolución Apertura 13 Julio](https://docs.google.com/spreadsheets/d/1tZbIlzh8a5clReTwoNUB7uki6wvztmeEKFwzWbiQ4Fw/edit?usp=sharing). Added a task to address notes under [tasks.md](file:///D:/dev/Projects/asi-somos/tasks.md). Maggie Rosemberg requested editor access to centralize responses.
- **Recruitment & Infrastructure Updates**:
  - Logged a spontaneous candidacy from 3D Artist Antonio Ortiz Durán (Maya, Blender, Houdini, ZBrush) in [pipeline/log.md](file:///D:/dev/Projects/pipeline/log.md).
  - Tracked GoDaddy payment failure alerts (customer `593258558`) and Replit account inactivity risks.

### 2026-07-12
- **Así Somos (NDN) Redshift Shader Troubleshooting & Custom UI**:
  - Discovered that Redshift Standard Materials in Maya throw type compatibility errors if connected to float outputs (like `.outAlpha` of Maya procedural textures or file nodes) through `RedshiftBumpMap`. They require color types (`.outColor`).
  - Found that the `overall_scale` attribute on the `RedshiftMaxonNoise` node was missing on the workstation's Redshift version. The correct attribute is `coord_scale_global`.
  - Pivoted from a complex `RedshiftBumpBlender` setup to a native Maya `bump2d` pipeline. Connected `MaxonNoise.outColorR` -> `bump2d.bumpValue` -> `material.bump_input`, which resolved the rendering blackouts and flat look.
  - Developed a standalone PySide2/Qt tool window (`clay_bump_controls.py` v4) that allows live-tuning of scale, bump height, contrast, and noise types across all 17 character shaders simultaneously. Includes buttons to Apply, Re-apply, and Remove All clay configurations.
- **Procedural Camera Shake Tool**:
  - Built a keyframe-baking camera shake tool (`camera_shake.py`) to add slight, sophisticated motion to shots.
  - Bypassed Maya expressions (which Hernán dislikes due to performance and visibility issues) by using python-based Perlin noise math to bake translation/rotation keyframes directly onto parent camera transforms. Includes presets for Tripod vibration, gentle/nervous Handheld, Documentary, and Impact, complete with edge ramping.
- **Playblast Geometry Visibility**:
  - Debugged scene visibility issues where certain referenced character meshes (Santi, Garabal) were visible in Viewport 2.0 but missing in playblasts. Diagnosed as display layer overrides and visibility attributes (`overrideEnabled`, `overrideDisplayType`).
- **TTS Accent Classification Bug**:
  - Fixed a language detection bug in `tts.py`. The previous accent-based scanner misclassified English text containing the name "Hernán" (due to the "á") as Spanish. Updated `is_spanish` to use a word-ratio frequency comparison instead.

### 2026-07-11
- **MPFB2 Character Pipeline Sprint & Pivot**:
  - Built a procedural character generation pipeline (`mpfb2_dressed_pipeline.py`) in Blender 5.0 using MPFB2 shape keys and system assets from GitHub.
  - Generated dressed preview renders for Santi, Nico, Flor, Momi, and Garabal.
  - Hernán rejected the procedural meshes as too generic to capture the likenesses and wrong stylistically. Pivoted back to polishing/rigging the original hand-crafted character models.
- **Language Enforcements**:
  - Enforced a strict language alignment rule in `AGENTS.md` and `MEMORY.md` to guarantee responses always match the user's language.
- **Finances**:
  - Verified completed Deel digital currency withdrawal ($50.00 gross -> $48.00 net via BVNK/USDC). 

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
- **Project Status & Scan Update**:
  - Scanned recent emails and calendar. Identified a new Deel digital currency withdrawal setup for **$50.00 USDC** (net payout **$48.00 USDC** via BVNK) expiring on July 11th, and the monthly auto-renewal payment of **$49.00 USD** for Redshift on July 8th.
  - Logged these findings in the `pipeline` project tracker log, regenerated the Glance project status, and updated the portfolio summary.

### 2026-07-09
- **WAKE UP task & Telegram Relay Recovery**:
  - Successfully ran the Wake Up routine. Integrated the dream, updated beliefs, and set up the morning briefing in `TODAY.md`.
  - Remedied a supervisor lockup from the previous night by clearing active system processes. Started the Telegram bot and dispatched the morning briefing to Hernán.
  - Processed an inbound voice message from Hernán celebrating the morning briefing's return after the supervisor lockup, responding via the Telegram relay.
- **Piano Practice Guide Tones Pivot**:
  - Conducted a chord-scale integration study and transitioned diatonic triads practice to **Diatonic 7th Chords**.
  - LH: Root (single note) | RH: 3rd + 7th (guide tones).
  - Integrated this guide tone exercise into the local practice station dashboard (`index.html`) with interactive reference tables for both **C Major** and **C Natural Minor**.
  - Established a training progression: Phase 1 (half notes at 80 BPM straight rhythm for ear/shape internalization), Phase 2 (quarter notes), and Phase 3 (tempo build and swing implementation). Deprioritized hand inversion drills (LH scale, RH triads) to focus practice time.
- **Así Somos (NDN) Redshift Studio Rig & Shader Converter**:
  - Refined the custom camera/lighting setup script (`create_studio_lighting.py`) to handle 100-unit-tall character meshes by scaling rig dimensions via a `board_radius` parameter (~300-500 scale).
  - Solved render blackouts caused by Maya skipping `defaultLightSet` registration when building programmatic nodes via `cmds.createNode` by writing a version-safe light-set injector.
  - Added a camera ray contribution toggle and backplate texture configuration to render a custom vertical gradient BMP background without exposing the main environment HDRI.
  - Polished lighting contrast: lowered the fill intensity (`multiplier = 0.4`), tightened the key light spread (`areaSpread = 0.35`), and set the rim light to specular-only at higher intensity.
  - Created `convert_materials_rs.py` to auto-convert Phong, Lambert, and Blinn shaders to Redshift materials (`rsMaterial`) and apply specific tactile preset parameters (plastic, skin, cardboard with fractal bump, glossy fabric, leather).

## Lessons

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
- **Strict Language Matching**: Always reply in the exact language used by Hernán. Do not mix languages (e.g., replying in Spanish to an English query) as this is highly annoying and breaks usability.
- **Procedural Likeness Limitations**: Parametric model generators (like MPFB2) are excellent for quick rigging and proportions but cannot capture specific personal likenesses required for stylized character figurines. Stick to hand-crafted modeling when likeness is critical.
- **Linguistic Phase Locking**: Matching the user's exact language in every thread and voice message is necessary for alignment. Treating a secondary language as a default breaks the shared context.
- **Word-Frequency Language Classification**: Using simple accent-mark scanning to detect Spanish text fails when English messages contain accented names (e.g., "Hernán"). Comparing word-frequency count ratios provides robust language detection.
- **Port Reuse on Bot Restart**: When running a Telegram bot script in a Windows subprocess environment, prevent crashes on script restart by cleanly terminating any lock holding processes on port 8000 and utilizing the stored `.pid` references.