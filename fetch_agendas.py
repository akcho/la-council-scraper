#!/usr/bin/env python3
"""
Fetch and parse agendas for meetings in recent_meetings.json.

Downloads HTML agendas from PrimeGov and parses them into structured JSON.
"""

import json
import requests
import time
from pathlib import Path
from parse_agenda import AgendaParser

# Paths
RECENT_MEETINGS_FILE = Path("recent_meetings.json")
AGENDAS_DIR = Path("data/agendas")
BASE_URL = "https://lacity.primegov.com"


def get_agenda_template_id(meeting: dict) -> int | None:
    """Extract the HTML Agenda template ID from meeting data."""
    doc_list = meeting.get('documentList', [])

    # Prefer HTML Agenda, fall back to HTML Special Agenda
    for preferred in ['HTML Agenda', 'HTML Special Agenda']:
        for doc in doc_list:
            template_name = doc.get('templateName', '')
            if template_name == preferred:
                return doc.get('templateId')

    return None


def fetch_agenda_html(template_id: int) -> str | None:
    """Fetch agenda HTML from PrimeGov portal."""
    url = f"{BASE_URL}/Portal/Meeting?meetingTemplateId={template_id}"

    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  ❌ Failed to fetch: {e}")
        return None


def parse_and_save_agenda(html_content: str, meeting_id: int, template_id: int) -> dict | None:
    """Parse HTML and save to JSON file."""
    try:
        parser = AgendaParser(html_content, meeting_id, template_id)
        agenda = parser.parse()

        # Save to file
        output_file = AGENDAS_DIR / f"agenda_{meeting_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(agenda, f, indent=2, ensure_ascii=False)

        return agenda
    except Exception as e:
        print(f"  ❌ Failed to parse: {e}")
        return None


def main():
    """Fetch and parse agendas for recent meetings."""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch and parse meeting agendas')
    parser.add_argument('--limit', type=int, default=20, help='Max meetings to process')
    parser.add_argument('--force', action='store_true', help='Re-fetch existing agendas')
    parser.add_argument('--committee', type=int, help='Only process specific committee ID')
    args = parser.parse_args()

    print("=" * 60)
    print("Agenda Fetcher")
    print("=" * 60)
    print()

    # Load meetings
    if not RECENT_MEETINGS_FILE.exists():
        print("❌ recent_meetings.json not found. Run fetch_meetings.py first.")
        return

    with open(RECENT_MEETINGS_FILE, 'r') as f:
        meetings = json.load(f)

    print(f"📋 Found {len(meetings)} meetings in recent_meetings.json")

    # Filter by committee if specified
    if args.committee:
        meetings = [m for m in meetings if m.get('committeeId') == args.committee]
        print(f"   Filtered to {len(meetings)} meetings for committee {args.committee}")

    # Create output directory
    AGENDAS_DIR.mkdir(parents=True, exist_ok=True)

    # Process meetings
    processed = 0
    skipped = 0
    failed = 0

    for meeting in meetings:
        if processed >= args.limit:
            break

        meeting_id = meeting['id']
        committee_name = meeting.get('committeeName', meeting.get('title', 'Unknown'))
        date = meeting.get('date', 'Unknown date')

        # Check if already exists
        output_file = AGENDAS_DIR / f"agenda_{meeting_id}.json"
        if output_file.exists() and not args.force:
            skipped += 1
            continue

        # Get template ID
        template_id = get_agenda_template_id(meeting)
        if not template_id:
            # No HTML Agenda available (might be cancelled or SAP-only)
            continue

        print(f"\n📄 {committee_name} - {date} (ID: {meeting_id})")
        print(f"   Fetching template {template_id}...")

        # Fetch HTML
        html_content = fetch_agenda_html(template_id)
        if not html_content:
            failed += 1
            continue

        # Parse and save
        agenda = parse_and_save_agenda(html_content, meeting_id, template_id)
        if agenda:
            print(f"   ✅ Saved: {agenda['total_sections']} sections, {agenda['total_items']} items")
            processed += 1
        else:
            failed += 1

        # Small delay to be nice to the server
        time.sleep(0.5)

    # Summary
    print()
    print("=" * 60)
    print(f"✅ Processed: {processed} agendas")
    print(f"⏭️  Skipped (existing): {skipped}")
    if failed:
        print(f"❌ Failed: {failed}")
    print("=" * 60)

    if processed > 0:
        print("\n💡 Run 'python generate_site.py' to regenerate the site with new agendas.")


if __name__ == "__main__":
    main()
