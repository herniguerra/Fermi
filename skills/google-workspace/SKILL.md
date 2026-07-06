---
name: google-workspace
description: >
  Access Hernán's Google Workspace (email, calendar) via OAuth.
  Activate when checking emails, calendar events, or scheduling.
  Trigger on: "check email", "check calendar", "what's on my schedule",
  "any new emails", "upcoming events", "morning briefing", "today's schedule".
---

# Google Workspace Integration

Fetches emails and calendar events from Hernán's Google Workspace account (`hernan.g@many-worlds.com`).

## Scripts

### Email
```bash
python C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/google-workspace/scripts/email_fetch.py [OPTIONS]
```

| Flag | Description |
|---|---|
| `--days N` | Fetch emails from the last N days |
| `--first-run` | First run: last 14 days, resets scan timestamp |
| `--max N` | Max emails to fetch (default: 100) |
| *(no flags)* | Incremental: emails since last scan |

### Calendar
```bash
python C:/Users/hernan.g/.gemini/config/plugins/fermi/skills/google-workspace/scripts/calendar_fetch.py [OPTIONS]
```

| Flag | Description |
|---|---|
| `--past-days N` | How many days back (default: 1) |
| `--future-days N` | How many days forward (default: 30) |
| `--max N` | Max events (default: 200) |

## Output

Both scripts output structured JSON to stdout. Parse it directly.

## Credentials

OAuth tokens and client secret are stored in:
```
D:/dev/Projects/.credentials/
├── client_secret.json
├── calendar_token.json
├── gmail_token.json
└── last_email_scan.txt
```

All scripts reference this shared credentials directory. Tokens auto-refresh.

## Common Patterns

### Morning briefing
```bash
# Today's calendar
python .../calendar_fetch.py --past-days 0 --future-days 1

# Recent emails
python .../email_fetch.py --days 1
```

### Weekly review
```bash
python .../calendar_fetch.py --past-days 7 --future-days 7
python .../email_fetch.py --days 7
```
