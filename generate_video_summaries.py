#!/usr/bin/env python3
"""
Generate video summaries for LA City Council meetings.

This script:
1. Reads agenda files to get video URLs
2. Downloads transcripts using get_transcripts.py
3. Generates AI summaries using summarize_meeting.py
4. Saves summaries to data/video_summaries/
"""

import os
import json
import glob
import sys
import time
from pathlib import Path
from get_transcripts import get_youtube_transcript
from summarize_meeting import summarize_with_claude
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directories
AGENDAS_DIR = Path("data/agendas")
SUMMARIES_DIR = Path("data/video_summaries")


def ensure_data_dirs():
    """Create necessary data directories."""
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)


def process_meeting_video(meeting_id: int, video_url: str, force: bool = False) -> bool:
    """
    Process video for a single meeting: download transcript and generate summary.

    Args:
        meeting_id: Meeting ID
        video_url: YouTube video URL
        force: If True, regenerate even if summary exists

    Returns:
        True if successful, False otherwise
    """
    summary_file = SUMMARIES_DIR / f"meeting_{meeting_id}_summary.json"

    # Skip if already processed (unless force=True)
    if summary_file.exists() and not force:
        print(f"  ⏭️  Summary already exists (use --force to regenerate)")
        return True

    print(f"  📺 Video URL: {video_url}")

    # Download transcript
    print(f"  📥 Downloading transcript...")
    transcript = get_youtube_transcript(video_url)

    if not transcript:
        print(f"  ❌ Failed to download transcript")
        return False

    print(f"  ✅ Got transcript: {len(transcript):,} characters")

    # Generate summary
    print(f"  🤖 Generating AI summary...")
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            print(f"  ❌ ANTHROPIC_API_KEY not set")
            return False

        summary = summarize_with_claude(transcript, api_key)
        print(f"  ✅ Generated summary: {len(summary)} characters")

        # Save summary as JSON
        summary_data = {
            'meeting_id': meeting_id,
            'video_url': video_url,
            'summary': summary,
            'transcript_length': len(transcript)
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        print(f"  💾 Saved to {summary_file}")

        # Add delay to avoid rate limits (120 seconds for long transcripts)
        print(f"  ⏳ Waiting 120 seconds to avoid rate limits...")
        time.sleep(120)

        return True

    except Exception as e:
        print(f"  ❌ Error generating summary: {e}")

        # If rate limited, wait and let caller retry
        if "rate_limit" in str(e).lower():
            print(f"  ⏳ Rate limited - waiting 120 seconds...")
            time.sleep(120)

        return False


def main():
    """Process all meeting videos."""

    print("=" * 60)
    print("LA Council Video Summary Generator")
    print("=" * 60)
    print()

    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set!")
        print("\nTo use this script:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("\nGet an API key at: https://console.anthropic.com/")
        sys.exit(1)

    # Parse command line args
    force = '--force' in sys.argv

    # Ensure directories exist
    ensure_data_dirs()

    # Get all agenda files
    agenda_files = sorted(AGENDAS_DIR.glob("agenda_*.json"))

    if not agenda_files:
        print("❌ No agenda files found in data/agendas/")
        sys.exit(1)

    print(f"📋 Found {len(agenda_files)} meeting(s)\n")

    # Process each meeting
    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, agenda_file in enumerate(agenda_files, 1):
        with open(agenda_file, 'r', encoding='utf-8') as f:
            agenda = json.load(f)

        meeting_id = agenda.get('meeting_id')
        video_url = agenda.get('video_url')

        print(f"[{i}/{len(agenda_files)}] Meeting {meeting_id}:")

        if not video_url:
            print(f"  ⚠️  No video URL available")
            skip_count += 1
            continue

        if process_meeting_video(meeting_id, video_url, force):
            success_count += 1
        else:
            fail_count += 1

        print()

    # Summary
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"✅ Successfully processed: {success_count}")
    print(f"⏭️  Skipped (no video): {skip_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📁 Summaries saved to: {SUMMARIES_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
