#!/usr/bin/env python3
"""
Get transcripts from YouTube videos using yt-dlp.
"""

import json
import subprocess
import re
from typing import Optional

def parse_vtt(vtt_content: str) -> str:
    """Parse VTT subtitle file and extract text only."""

    lines = []
    for line in vtt_content.split('\n'):
        # Skip WEBVTT header, timestamps, and blank lines
        line = line.strip()
        if (not line or
            line.startswith('WEBVTT') or
            '-->' in line or
            line.isdigit() or
            re.match(r'^\d{2}:', line)):  # Skip timestamp lines
            continue

        # Remove HTML tags if any
        line = re.sub(r'<[^>]+>', '', line)
        if line:
            lines.append(line)

    return ' '.join(lines)

def get_youtube_transcript(video_url: str) -> Optional[str]:
    """
    Download auto-generated captions from YouTube video.
    Uses yt-dlp to extract subtitles.
    """

    if not video_url:
        return None

    print(f"📺 Fetching transcript from {video_url}...")

    try:
        # Use yt-dlp to get auto-generated captions
        cmd = [
            'yt-dlp',
            '--skip-download',  # Don't download video
            '--write-auto-subs',  # Get auto-generated captions
            '--sub-lang', 'en',  # English
            '--sub-format', 'vtt',  # WebVTT format
            '--output', 'transcript',  # Output filename
            video_url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Read the generated VTT file
            try:
                with open('transcript.en.vtt', 'r', encoding='utf-8') as f:
                    vtt_content = f.read()

                # Parse VTT to extract just the text
                transcript = parse_vtt(vtt_content)
                print(f"✅ Got transcript: {len(transcript)} characters")
                return transcript
            except FileNotFoundError:
                print("⚠️  Transcript file not found")
                return None
        else:
            print(f"❌ yt-dlp error: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print("❌ Timeout while fetching transcript")
        return None
    except FileNotFoundError:
        print("❌ yt-dlp not installed. Install with: pip install yt-dlp")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Test transcript fetching."""

    print("=" * 60)
    print("YouTube Transcript Fetcher")
    print("=" * 60)
    print()

    # Load recent meetings
    try:
        with open('recent_meetings.json', 'r') as f:
            meetings = json.load(f)
    except FileNotFoundError:
        print("❌ Run fetch_meetings.py first!")
        return

    # Get transcript for the most recent meeting with a video
    for meeting in meetings:
        video_url = meeting.get('videoUrl')
        if video_url:
            print(f"Meeting: {meeting['title']}")
            print(f"Date: {meeting['date']}")
            print(f"Video: {video_url}\n")

            transcript = get_youtube_transcript(video_url)

            if transcript:
                # Save transcript
                meeting_id = meeting['id']
                filename = f"meeting_{meeting_id}_transcript.txt"

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(transcript)

                print(f"💾 Saved transcript to {filename}")
                print(f"\n📝 First 500 characters:")
                print(transcript[:500])
                print("...\n")

                break  # Just test with one meeting for now

    print("=" * 60)


if __name__ == "__main__":
    main()
