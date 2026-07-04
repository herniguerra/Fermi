# Fermi

Hernán's AI assistant — persona, memory system, and Telegram relay for Antigravity.

## What is this?

This repo is Fermi's source code — the plugin that defines who Fermi is and how it operates. It lives at `C:\Users\hernan.g\.gemini\config\plugins\fermi\` (symlinked from this repo) and is auto-loaded by Antigravity in every session.

## Architecture

```
fermi/
├── plugin.json              # Plugin metadata
├── memory/
│   ├── USER.md              # Hernán's profile & preferences
│   └── MEMORY.md            # Learned facts & running context
├── skills/
│   ├── fermi-memory/        # Memory management skill
│   │   └── SKILL.md
│   └── telegram-relay/      # Telegram bot relay skill
│       ├── SKILL.md
│       └── scripts/
│           ├── bot.py
│           └── config.json
└── media/
    └── outbox.jsonl          # Telegram outbox
```

The core identity lives in the global `AGENTS.md` at `~/.gemini/config/AGENTS.md`, not in this repo — it's loaded automatically by Antigravity and kept lean.

## Design

Inspired by OpenClaw's SOUL.md pattern and Hermes Agent's nudge system:

- **Identity** (AGENTS.md) — Who Fermi is. Stable, rarely changes.
- **Memory** (USER.md + MEMORY.md) — What Fermi knows. Living documents, periodically compacted.
- **Skills** (SKILL.md files) — How Fermi does things. Procedural knowledge.

## Named after

[Enrico Fermi](https://en.wikipedia.org/wiki/Enrico_Fermi) — the physicist who built the first nuclear reactor in a squash court and whose estimation techniques ("Fermi problems") cut through complexity with elegant reasoning. Also ties to Many-Worlds: quantum foundations, superposition, and the aesthetics of uncertainty.
