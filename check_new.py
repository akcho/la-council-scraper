#!/usr/bin/env python3
"""
Quick check: Is there a new meeting ready to summarize?
"""

import json
from datetime import datetime, timedelta
from fetch_meetings import LACouncilScraper

def main():
    print("🔍 Checking for new City Council meetings...\n")

    scraper = LACouncilScraper()
    meetings = scraper.get_recent_meetings(limit=10)

    if not meetings:
        print("❌ No meetings found")
        return

    # Find the most recent meeting with a video
    meeting_with_video = None
    for meeting in meetings:
        if meeting.get('videoUrl'):
            meeting_with_video = meeting
            break

    if meeting_with_video:
        meeting_date = meeting_with_video.get('date', 'Unknown')
        video_url = meeting_with_video.get('videoUrl')
        meeting_id = meeting_with_video.get('id')

        print(f"✅ Latest meeting with video available:")
        print(f"   📅 Date: {meeting_date}")
        print(f"   🆔 ID: {meeting_id}")
        print(f"   📺 Video: {video_url}")
        print(f"\n🚀 Ready to summarize!")
        print(f"\nRun: ./summarize.sh")
    else:
        latest = meetings[0]
        meeting_date = latest.get('date', 'Unknown')
        print(f"📅 Most recent meeting: {meeting_date}")
        print(f"📺 Video: Not uploaded yet")
        print(f"\n⏳ No videos available yet. Check back later.")
        print(f"   (Videos usually upload within 24 hours of the meeting)")

if __name__ == "__main__":
    main()
