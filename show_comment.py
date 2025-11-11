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

    print(content)

    # Try to copy to clipboard
    try:
        import subprocess
        subprocess.run('pbcopy', text=True, input=content, check=True)
        print("\n✅ Copied to clipboard!")
    except:
        pass

if __name__ == "__main__":
    main()
