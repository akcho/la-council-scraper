#!/usr/bin/env python3
"""
Full pipeline: Fetch meetings -> Get transcripts -> Summarize
Run this after each City Council meeting to generate a summary.
"""

import subprocess
import sys
import os
import glob
from datetime import datetime

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Error in: {description}")
        sys.exit(1)
    return result.returncode == 0

def cleanup_generated_files():
    """
    Clean up generated files after successful pipeline run.
    These files are posted to Reddit, so we don't need local copies.
    """
    print(f"\n{'='*60}")
    print("🧹 Cleaning up generated files")
    print(f"{'='*60}\n")

    patterns = [
        'meeting_*_transcript.txt',
        'meeting_*_summary.txt',
        'meeting_*_reddit_comment.md',
        'meeting_*_agenda.html',
        'transcript.en.vtt',  # Temporary VTT file from yt-dlp
        'recent_meetings.json'  # API data used to pass between pipeline steps
    ]

    files_deleted = 0
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
                print(f"   Deleted: {filepath}")
                files_deleted += 1
            except OSError as e:
                print(f"   ⚠️  Could not delete {filepath}: {e}")

    if files_deleted > 0:
        print(f"\n✅ Cleaned up {files_deleted} file(s)")
    else:
        print("   No generated files found to clean up")

    print()

def main():
    """Run the full pipeline."""

    print("=" * 60)
    print("LA City Council Summarizer - Full Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Fetch latest meetings
    run_command(
        "python fetch_meetings.py",
        "Step 1/3: Fetching latest City Council meetings"
    )

    # Step 2: Get transcript for most recent meeting
    run_command(
        "python get_transcripts.py",
        "Step 2/3: Downloading YouTube transcript"
    )

    # Step 3: Generate AI summary
    run_command(
        "python summarize_meeting.py",
        "Step 3/3: Generating AI summary"
    )

    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE!")
    print("=" * 60)
    print("\nYour Reddit comment is ready to post!")
    print("Check the output above for the formatted comment.")
    print("\n" + "=" * 60)

    # Clean up generated files since they're posted to Reddit
    cleanup_generated_files()

if __name__ == "__main__":
    main()
