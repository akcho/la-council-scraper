#!/usr/bin/env python3
"""
Send weekly newsletter via Buttondown API.

Usage:
    python send_newsletter.py           # Interactive mode
    python send_newsletter.py --draft   # Save as draft (no prompt)
    python send_newsletter.py --send    # Send immediately (no prompt)
    python send_newsletter.py --preview # Preview only, don't send
"""

import os
import sys
import glob
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BUTTONDOWN_API_KEY = os.environ.get('BUTTONDOWN_API_KEY')
BUTTONDOWN_API_URL = "https://api.buttondown.com/v1/emails"


def get_newsletter_blurbs() -> list[str]:
    """Find all newsletter blurb files and return their contents."""
    blurbs = []
    for filepath in sorted(glob.glob("meeting_*_newsletter.txt")):
        with open(filepath, 'r', encoding='utf-8') as f:
            blurbs.append(f.read())
    return blurbs


def compose_newsletter(blurbs: list[str]) -> tuple[str, str]:
    """
    Compose the full newsletter from individual meeting blurbs.

    Returns:
        Tuple of (subject, body)
    """
    today = datetime.now()
    week_of = today.strftime("%B %d, %Y")

    subject = f"Week of {week_of}"

    # Compose body with all blurbs
    body_parts = [
        "Here's what happened in LA City Council this week:\n",
        "---\n"
    ]

    for blurb in blurbs:
        body_parts.append(blurb)
        body_parts.append("\n\n---\n")

    body_parts.append("\n*You're receiving this because you subscribed to Council Reader. [Unsubscribe]({{ unsubscribe_url }})*")

    body = "\n".join(body_parts)

    return subject, body


def send_newsletter(subject: str, body: str, draft: bool = True) -> dict:
    """
    Send newsletter via Buttondown API.

    Args:
        subject: Email subject line
        body: Email body (markdown supported)
        draft: If True, saves as draft instead of sending immediately

    Returns:
        API response as dict
    """
    if not BUTTONDOWN_API_KEY:
        raise ValueError("BUTTONDOWN_API_KEY environment variable not set")

    headers = {
        "Authorization": f"Token {BUTTONDOWN_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "subject": subject,
        "body": body,
        "status": "draft" if draft else "about_to_send"
    }

    response = requests.post(BUTTONDOWN_API_URL, headers=headers, json=data)
    response.raise_for_status()

    return response.json()


def main():
    """Compose and send the weekly newsletter."""

    print("=" * 60)
    print("Council Reader Newsletter")
    print("=" * 60)
    print()

    if not BUTTONDOWN_API_KEY:
        print("BUTTONDOWN_API_KEY environment variable not set!")
        print("\nTo use this script:")
        print("  export BUTTONDOWN_API_KEY='your-key-here'")
        print("\nGet your API key at: https://buttondown.com/settings/programming")
        return

    # Find newsletter blurbs
    blurbs = get_newsletter_blurbs()

    if not blurbs:
        print("No newsletter blurbs found!")
        print("Run summarize_meeting.py first to generate meeting summaries.")
        return

    print(f"Found {len(blurbs)} meeting summary(ies)")

    # Compose newsletter
    subject, body = compose_newsletter(blurbs)

    print(f"\nSubject: {subject}")
    print("\n" + "=" * 60)
    print("PREVIEW")
    print("=" * 60)
    print(body)
    print("=" * 60)

    # Check for command-line flags
    if '--preview' in sys.argv:
        print("\n(Preview mode - not sending)")
        return

    if '--draft' in sys.argv:
        choice = 'd'
        print("\n(Auto-saving as draft)")
    elif '--send' in sys.argv:
        choice = 's'
        print("\n(Auto-sending immediately)")
    else:
        # Interactive mode
        print("\nOptions:")
        print("  [d] Save as draft (review in Buttondown before sending)")
        print("  [s] Send immediately to all subscribers")
        print("  [q] Quit without sending")

        choice = input("\nChoice [d/s/q]: ").strip().lower()

        if choice == 'q':
            print("Cancelled.")
            return

    draft = choice != 's'

    try:
        result = send_newsletter(subject, body, draft=draft)

        if draft:
            print(f"\nDraft saved! Review at: https://buttondown.com/emails")
        else:
            print(f"\nNewsletter sent to subscribers!")

        print(f"Email ID: {result.get('id', 'unknown')}")

    except requests.exceptions.HTTPError as e:
        print(f"\nAPI Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
