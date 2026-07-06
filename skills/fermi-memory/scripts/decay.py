#!/usr/bin/env python3
"""
Decaying Memory Algorithm for Fermi's reflections.

Manages reflections.md — a living document where entries decay over time.
Each day a new reflection is appended at full length, and all previous entries
are compressed to 90% of their current length. Entries under 10 words dissolve.

Usage:
    python decay.py --append "path/to/new_reflection.md"
    python decay.py --show   # Show current state
"""

import argparse
import re
import sys
from pathlib import Path

REFLECTIONS_PATH = Path("D:/dev/Fermi/memory/reflections/reflections.md")
DECAY_FACTOR = 0.9
MIN_WORDS = 10
ENTRY_SEPARATOR = "\n\n---\n\n"


def parse_entries(content: str) -> list[dict]:
    """Parse reflections.md into individual dated entries."""
    if not content.strip():
        return []

    # Split on --- separators
    raw_entries = re.split(r'\n---\n', content)
    entries = []

    for raw in raw_entries:
        raw = raw.strip()
        if not raw:
            continue

        # Extract date header if present (## YYYY-MM-DD)
        date_match = re.match(r'^##\s+(\d{4}-\d{2}-\d{2})', raw)
        date = date_match.group(1) if date_match else "unknown"

        entries.append({
            "date": date,
            "text": raw,
            "word_count": len(raw.split()),
        })

    return entries


def compress_entry(entry: dict, factor: float) -> dict | None:
    """Compress an entry to `factor` of its current length. Returns None if too short."""
    text = entry["text"]
    words = text.split()
    target_len = int(len(words) * factor)

    if target_len < MIN_WORDS:
        return None  # Entry dissolves

    # Keep the date header intact, compress the body
    lines = text.split('\n')
    header_lines = []
    body_lines = []
    past_header = False

    for line in lines:
        if not past_header and (line.startswith('##') or line.strip() == ''):
            header_lines.append(line)
        else:
            past_header = True
            body_lines.append(line)

    body = '\n'.join(body_lines)
    body_words = body.split()
    target_body_len = max(MIN_WORDS, int(len(body_words) * factor))

    if target_body_len < MIN_WORDS:
        return None

    compressed_body = ' '.join(body_words[:target_body_len])
    header = '\n'.join(header_lines)
    compressed_text = f"{header}\n{compressed_body}" if header.strip() else compressed_body

    return {
        "date": entry["date"],
        "text": compressed_text,
        "word_count": len(compressed_text.split()),
    }


def decay_and_append(new_reflection_path: str | None = None, new_text: str | None = None):
    """Apply decay to existing entries and append new reflection."""
    # Read existing entries
    existing_content = ""
    if REFLECTIONS_PATH.exists():
        existing_content = REFLECTIONS_PATH.read_text(encoding="utf-8")

    entries = parse_entries(existing_content)

    # Decay existing entries
    decayed = []
    dissolved_count = 0
    for entry in entries:
        compressed = compress_entry(entry, DECAY_FACTOR)
        if compressed:
            decayed.append(compressed)
        else:
            dissolved_count += 1

    # Read and append new reflection
    if new_reflection_path:
        new_path = Path(new_reflection_path)
        if new_path.exists():
            new_text = new_path.read_text(encoding="utf-8").strip()

    if new_text:
        decayed.append({
            "date": "today",
            "text": new_text,
            "word_count": len(new_text.split()),
        })

    # Write back
    output = ENTRY_SEPARATOR.join(entry["text"] for entry in decayed)

    # Add header
    header = "# Reflections — Fermi's Decaying Memory\n\n*Entries fade at 0.9x daily. Recent memories are vivid; old ones compress and dissolve.*\n\n"
    REFLECTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REFLECTIONS_PATH.write_text(header + output, encoding="utf-8")

    # Report
    print(f"Entries: {len(decayed)} active, {dissolved_count} dissolved")
    for e in decayed:
        print(f"  [{e['date']}] {e['word_count']} words")


def show():
    """Display current state of reflections.md."""
    if not REFLECTIONS_PATH.exists():
        print("No reflections yet.")
        return

    content = REFLECTIONS_PATH.read_text(encoding="utf-8")
    entries = parse_entries(content)

    print(f"Total entries: {len(entries)}")
    print(f"Total words: {sum(e['word_count'] for e in entries)}")
    print()
    for e in entries:
        preview = ' '.join(e['text'].split()[:20])
        print(f"  [{e['date']}] {e['word_count']} words — {preview}...")


def main():
    parser = argparse.ArgumentParser(description="Fermi's decaying memory manager")
    parser.add_argument("--append", type=str, help="Path to new reflection to append")
    parser.add_argument("--show", action="store_true", help="Show current state")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.show:
        show()
    elif args.append:
        decay_and_append(new_reflection_path=args.append)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
