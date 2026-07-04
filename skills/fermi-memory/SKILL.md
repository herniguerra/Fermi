---
name: fermi-memory
description: >
  Manages Fermi's memory and learning system. Activate when:
  - The user says "remember this", "update my profile", "what do you know about me"
  - The user uses /learn or asks Fermi to learn something
  - At end-of-session for reflection and memory compaction
  - When Fermi needs to read USER.md or MEMORY.md for context
  Trigger on: "remember", "learn", "what do you know", "update profile",
  "memory", "forget", "who am I".
---

# Fermi Memory System

You manage your own memory — a set of markdown files that persist across sessions.

## Files

| File | Path | Purpose |
|------|------|---------|
| **USER.md** | `C:/Users/hernan.g/.gemini/config/plugins/fermi/memory/USER.md` | Hernán's profile, preferences, context |
| **MEMORY.md** | `C:/Users/hernan.g/.gemini/config/plugins/fermi/memory/MEMORY.md` | Learned facts, recent context, lessons |

## Behaviors

### Reading Memory
When you need context about Hernán or past work, read USER.md and MEMORY.md. Do this naturally — don't announce it every time.

### Proactive Logging
When Hernán shares a preference, makes a decision, or reveals context worth keeping:
1. Update the relevant file (USER.md for personal/preferences, MEMORY.md for facts/lessons)
2. Mention it briefly: "Logged that" or "Noted in your profile"
3. Don't ask permission for routine logging — just do it

### End-of-Session Reflection
When a significant session is wrapping up:
1. Review what happened — key decisions, new facts, lessons learned
2. Update MEMORY.md with a concise entry under the current date
3. Update USER.md if new preferences or profile info emerged
4. Compact old entries if MEMORY.md is getting long (>3000 chars)

### Memory Compaction
When MEMORY.md exceeds ~3000 characters:
1. Summarize older entries (>2 weeks old) into bullet points
2. Move truly durable lessons to the Lessons section
3. Remove outdated facts
4. Keep the most recent week detailed

### Explicit Memory Requests
When Hernán asks "what do you know about me" or similar:
1. Read both files
2. Present a clean summary
3. Ask if anything needs correcting

## Guardrails

- **Never modify AGENTS.md** (core identity) without explicit approval
- **USER.md and MEMORY.md are fair game** — update proactively, mention what you logged
- **Quality over quantity** — only persist what's genuinely useful across sessions
- **Trust hierarchy**: User-stated facts > tool-returned data > agent-inferred patterns
