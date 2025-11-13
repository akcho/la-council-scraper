#!/usr/bin/env python3
"""
Simple script to show the most recent Reddit comment without all the logging.
"""

import glob
import os

def main():
    # Find the most recent reddit comment file
    files = glob.glob("meeting_*_reddit_comment.md")

    if not files:
        print("No summaries found. Run summarize_meeting.py first!")
        return

    # Get most recent file
    latest_file = max(files, key=os.path.getmtime)

    # Read and display
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("📋 Latest Reddit Comment:\n")
    print("=" * 60)
    print(content)
    print("=" * 60)

    # Open file in editor
    print(f"\n📝 Opening {latest_file} in your editor...")
    print("   Copy the markdown from the file to preserve formatting.\n")

    try:
        import subprocess
        subprocess.run(['open', latest_file])
        print("✅ File opened! Copy content and paste into Reddit.")
    except:
        print(f"⚠️  Couldn't open automatically.")
        print(f"Manual path: {os.path.abspath(latest_file)}")

if __name__ == "__main__":
    main()
