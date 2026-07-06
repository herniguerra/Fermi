#!/usr/bin/env python3
"""
Fetches upcoming and recent calendar events from a Google Workspace account.
Outputs structured JSON to stdout for the project tracker agent to review.

Usage:
    python calendar_fetch.py                   # Default: past 24h + next 30 days
    python calendar_fetch.py --past-days 7     # Past 7 days + next 30 days
    python calendar_fetch.py --future-days 60  # Past 24h + next 60 days
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Google API imports — installed via: pip install google-api-python-client google-auth-oauthlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

CREDENTIALS_DIR = Path("D:/dev/Projects/.credentials")
CLIENT_SECRET = CREDENTIALS_DIR / "client_secret.json"
TOKEN_PATH = CREDENTIALS_DIR / "calendar_token.json"

DEFAULT_PAST_DAYS = 1
DEFAULT_FUTURE_DAYS = 30


def get_service():
    """Authenticate and return a Google Calendar API service instance."""
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

    return build("calendar", "v3", credentials=creds)


def fetch_events(
    service, time_min: datetime, time_max: datetime, max_results: int = 200
) -> list[dict]:
    """Fetch calendar events within the given time window."""
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    raw_events = events_result.get("items", [])
    events = []

    for event in raw_events:
        # Parse start/end — can be date or dateTime
        start = event.get("start", {})
        end = event.get("end", {})
        start_str = start.get("dateTime", start.get("date", ""))
        end_str = end.get("dateTime", end.get("date", ""))

        # Extract attendees
        attendees = []
        for a in event.get("attendees", []):
            attendee = {
                "email": a.get("email", ""),
                "name": a.get("displayName", ""),
                "response": a.get("responseStatus", ""),
            }
            if a.get("organizer"):
                attendee["organizer"] = True
            attendees.append(attendee)

        events.append(
            {
                "id": event.get("id", ""),
                "title": event.get("summary", "Untitled Event"),
                "start": start_str,
                "end": end_str,
                "location": event.get("location", ""),
                "description": (event.get("description", "") or "")[:500],
                "attendees": attendees,
                "status": event.get("status", ""),
                "html_link": event.get("htmlLink", ""),
                "is_all_day": "date" in start and "dateTime" not in start,
                "organizer": event.get("organizer", {}).get("email", ""),
            }
        )

    return events


def main():
    parser = argparse.ArgumentParser(
        description="Fetch calendar events for project tracker"
    )
    parser.add_argument(
        "--past-days",
        type=int,
        default=DEFAULT_PAST_DAYS,
        help=f"How many days back to look (default: {DEFAULT_PAST_DAYS})",
    )
    parser.add_argument(
        "--future-days",
        type=int,
        default=DEFAULT_FUTURE_DAYS,
        help=f"How many days forward to look (default: {DEFAULT_FUTURE_DAYS})",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=200,
        help="Maximum number of events to fetch (default: 200)",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    now = datetime.now(timezone.utc)
    time_min = now - timedelta(days=args.past_days)
    time_max = now + timedelta(days=args.future_days)

    service = get_service()
    events = fetch_events(service, time_min, time_max, max_results=args.max)

    # Split into past and upcoming for easier agent processing
    past_events = []
    upcoming_events = []
    for e in events:
        start_str = e.get("start", "")
        try:
            if "T" in start_str:
                start_dt = datetime.fromisoformat(start_str)
            else:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            if start_dt < now:
                past_events.append(e)
            else:
                upcoming_events.append(e)
        except (ValueError, TypeError):
            upcoming_events.append(e)  # Default to upcoming if can't parse

    output = {
        "scan_time": now.isoformat(),
        "window": {
            "from": time_min.isoformat(),
            "to": time_max.isoformat(),
        },
        "total_count": len(events),
        "past_events": past_events,
        "upcoming_events": upcoming_events,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
