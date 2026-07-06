#!/usr/bin/env python3
"""
Fetches recent emails from a Google Workspace Gmail account.
Outputs structured JSON to stdout for the project tracker agent to review.

Usage:
    python email_fetch.py                  # Emails since last scan
    python email_fetch.py --days 14        # Emails from last 14 days
    python email_fetch.py --first-run      # First run: last 14 days, resets timestamp
"""

import argparse
import json
import os
import sys
import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Google API imports — installed via: pip install google-api-python-client google-auth-oauthlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

CREDENTIALS_DIR = Path("D:/dev/Projects/.credentials")
CLIENT_SECRET = CREDENTIALS_DIR / "client_secret.json"
TOKEN_PATH = CREDENTIALS_DIR / "gmail_token.json"
LAST_SCAN_PATH = CREDENTIALS_DIR / "last_email_scan.txt"

DEFAULT_FIRST_RUN_DAYS = 14
MAX_RESULTS = 100  # Cap per scan to avoid overwhelming the agent


def get_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not CLIENT_SECRET.exists():
                print(
                    f"Error: {CLIENT_SECRET} not found. "
                    "Place your OAuth client secret JSON there.",
                    file=sys.stderr,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_last_scan_time() -> datetime | None:
    """Read the last scan timestamp, or None if never scanned."""
    if LAST_SCAN_PATH.exists():
        try:
            ts = LAST_SCAN_PATH.read_text().strip()
            return datetime.fromisoformat(ts)
        except Exception:
            pass
    return None


def save_scan_time(dt: datetime):
    """Persist the scan timestamp."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    LAST_SCAN_PATH.write_text(dt.isoformat())


def fetch_emails(service, after: datetime, max_results: int = MAX_RESULTS) -> list[dict]:
    """Fetch emails received after the given datetime."""
    # Gmail uses epoch seconds for after: query
    after_epoch = int(after.timestamp())
    query = f"after:{after_epoch}"

    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    message_ids = results.get("messages", [])

    emails = []
    for msg_ref in message_ids:
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg_ref["id"],
                format="full",
                metadataHeaders=["Subject", "From", "To", "Date", "Cc"],
            )
            .execute()
        )

        headers = msg.get("payload", {}).get("headers", [])
        header_map = {}
        for h in headers:
            name = h.get("name", "").lower()
            if name in ("subject", "from", "to", "date", "cc"):
                header_map[name] = h.get("value", "")

        # Extract body preview (plain text, first 800 chars)
        body_preview = _extract_body(msg.get("payload", {}))

        emails.append(
            {
                "id": msg_ref["id"],
                "date": header_map.get("date", ""),
                "from": header_map.get("from", ""),
                "to": header_map.get("to", ""),
                "cc": header_map.get("cc", ""),
                "subject": header_map.get("subject", "No Subject"),
                "snippet": msg.get("snippet", ""),
                "body_preview": body_preview[:800] if body_preview else "",
                "labels": msg.get("labelIds", []),
            }
        )

    return emails


def _extract_body(payload: dict, max_depth: int = 5) -> str:
    """Recursively extract plain text body from Gmail payload."""
    if max_depth <= 0:
        return ""

    mime = payload.get("mimeType", "")

    # Direct body
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            try:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            except Exception:
                return ""

    # Multipart — recurse into parts, prefer text/plain
    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "text/plain":
            result = _extract_body(part, max_depth - 1)
            if result:
                return result

    # Fallback: try any part
    for part in parts:
        result = _extract_body(part, max_depth - 1)
        if result:
            return result

    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Fetch recent Gmail emails for project tracker"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Override: fetch emails from the last N days",
    )
    parser.add_argument(
        "--first-run",
        action="store_true",
        help="First run mode: fetch last 14 days and reset scan timestamp",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=MAX_RESULTS,
        help=f"Maximum number of emails to fetch (default: {MAX_RESULTS})",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Determine the "after" cutoff
    now = datetime.now(timezone.utc)

    if args.days:
        after = now - timedelta(days=args.days)
    elif args.first_run:
        after = now - timedelta(days=DEFAULT_FIRST_RUN_DAYS)
    else:
        last_scan = get_last_scan_time()
        if last_scan:
            # Make timezone-aware if needed
            if last_scan.tzinfo is None:
                after = last_scan.replace(tzinfo=timezone.utc)
            else:
                after = last_scan
        else:
            # No previous scan — default to first run behavior
            after = now - timedelta(days=DEFAULT_FIRST_RUN_DAYS)

    service = get_service()
    emails = fetch_emails(service, after=after, max_results=args.max)

    output = {
        "scan_time": now.isoformat(),
        "after": after.isoformat(),
        "count": len(emails),
        "emails": emails,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))

    # Save scan timestamp
    save_scan_time(now)


if __name__ == "__main__":
    main()
