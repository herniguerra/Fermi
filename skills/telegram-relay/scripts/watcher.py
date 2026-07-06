#!/usr/bin/env python3
"""
Fermi Inbox Watcher — Lightweight file monitor for event-driven relay.

Watches inbox.jsonl for new messages and prints them to stdout.
When stdout is connected to an Antigravity background task, this triggers
agent notifications without constant AI polling.

Zero token usage while idle — just an os.stat() call every second.

Usage:
    python watcher.py [inbox_path]
"""

import os
import sys
import time
import json


def main():
    # Default inbox path
    inbox_path = sys.argv[1] if len(sys.argv) > 1 else \
        "C:/Users/hernan.g/.gemini/config/plugins/fermi/media/inbox.jsonl"

    # Ensure stdout is line-buffered for immediate notifications
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

    print(json.dumps({
        "type": "system",
        "event": "watcher_started",
        "inbox": inbox_path,
    }), flush=True)

    # Start at end of file if it exists (don't replay old messages)
    last_pos = 0
    if os.path.exists(inbox_path):
        last_pos = os.path.getsize(inbox_path)

    while True:
        try:
            if os.path.exists(inbox_path):
                size = os.path.getsize(inbox_path)

                if size > last_pos:
                    # New data! Read only the new lines
                    with open(inbox_path, "r", encoding="utf-8") as f:
                        f.seek(last_pos)
                        new_data = f.read()
                        last_pos = f.tell()

                    # Forward each new line to stdout (triggers agent wake)
                    for line in new_data.splitlines():
                        line = line.strip()
                        if line:
                            print(line, flush=True)

                elif size < last_pos:
                    # File was truncated/cleared — reset position
                    last_pos = 0

        except Exception as e:
            print(json.dumps({
                "type": "system",
                "event": "watcher_error",
                "error": str(e),
            }), flush=True)

        time.sleep(1)


if __name__ == "__main__":
    main()
