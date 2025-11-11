#!/usr/bin/env python3
"""
Summarize LA City Council meetings using Claude AI.
"""

import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SUMMARIZATION_PROMPT = """You are analyzing a transcript from a Los Angeles City Council meeting. Your job is to create a concise, accessible summary for regular citizens reading a Reddit comment.

Analyze the transcript and provide:

1. **KEY DECISIONS** (2-3 bullet points max)
   - What major decisions/votes happened?
   - Include vote results if mentioned
   - Focus on concrete outcomes only

2. **NOTABLE DISCUSSIONS** (2-3 bullet points max)
   - Main topics that impact residents
   - Only include truly newsworthy items
   - Skip routine/ceremonial business

3. **BOTTOM LINE** (1-2 sentences)
   - One clear takeaway for LA residents
   - Why does this matter?

Keep your summary:
- **Under 200 words total** (this will be a Reddit comment)
- Clear and jargon-free (explain any acronyms/technical terms)
- Focused on practical impact, not process
- Objective and factual (no political spin)
- Skip routine ceremonial items unless truly significant

If the meeting was mostly ceremonial (commendations, routine approvals), say so in one sentence and only highlight any actual substantive business."""

def summarize_with_claude(transcript: str, api_key: str = None) -> str:
    """
    Summarize meeting transcript using Claude API.

    Args:
        transcript: Full meeting transcript text
        api_key: Anthropic API key (or reads from ANTHROPIC_API_KEY env var)

    Returns:
        Formatted summary string
    """

    if not api_key:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    print("🤖 Sending transcript to Claude for summarization...")
    print(f"   Transcript length: {len(transcript):,} characters")

    client = Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # Latest Claude model
            max_tokens=800,  # Shorter for comment format
            temperature=0.3,  # Lower temp for more factual output
            messages=[
                {
                    "role": "user",
                    "content": f"{SUMMARIZATION_PROMPT}\n\n---\n\nTRANSCRIPT:\n\n{transcript}"
                }
            ]
        )

        summary = message.content[0].text
        print(f"✅ Got summary: {len(summary)} characters")

        return summary

    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        raise


def format_summary_for_reddit(meeting_info: dict, summary: str) -> str:
    """Format the summary as a Reddit comment for daily discussion thread."""

    title = meeting_info.get('title', 'LA City Council Meeting')
    date = meeting_info.get('date', 'Unknown Date')
    video_url = meeting_info.get('videoUrl', '')

    comment = f"""**{title} - {date}**

{summary}

📺 [Watch Meeting]({video_url}) | 📄 [View Agenda](https://lacity.primegov.com/Portal/Meeting?meetingTemplateId={meeting_info['id']})

---
*AI-generated summary to help LA residents stay informed. Feedback welcome!*"""

    return comment


def main():
    """Test summarization with a real meeting."""

    print("=" * 60)
    print("LA City Council Meeting Summarizer")
    print("=" * 60)
    print()

    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set!")
        print("\nTo use this script:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("\nGet an API key at: https://console.anthropic.com/")
        return

    # Load meeting data
    try:
        with open('recent_meetings.json', 'r') as f:
            meetings = json.load(f)
    except FileNotFoundError:
        print("❌ Run fetch_meetings.py first!")
        return

    # Find a meeting with a transcript
    meeting = meetings[0]  # Most recent
    meeting_id = meeting['id']
    transcript_file = f"meeting_{meeting_id}_transcript.txt"

    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript = f.read()
    except FileNotFoundError:
        print(f"❌ Transcript file not found: {transcript_file}")
        print("   Run get_transcripts.py first!")
        return

    print(f"📋 Meeting: {meeting['title']}")
    print(f"📅 Date: {meeting['date']}")
    print(f"📄 Transcript: {len(transcript):,} characters\n")

    # Summarize
    summary = summarize_with_claude(transcript, api_key)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60 + "\n")
    print(summary)
    print("\n" + "=" * 60)

    # Format for Reddit daily discussion comment
    reddit_comment = format_summary_for_reddit(meeting, summary)

    # Save both
    with open(f"meeting_{meeting_id}_summary.txt", 'w', encoding='utf-8') as f:
        f.write(summary)

    with open(f"meeting_{meeting_id}_reddit_comment.md", 'w', encoding='utf-8') as f:
        f.write(reddit_comment)

    print("\n💾 Saved:")
    print(f"   - meeting_{meeting_id}_summary.txt")
    print(f"   - meeting_{meeting_id}_reddit_comment.md")

    # Try to copy to clipboard
    try:
        import subprocess
        subprocess.run('pbcopy', text=True, input=reddit_comment, check=True)
        print("\n✅ Copied to clipboard! Just paste it into Reddit.")
    except:
        print("\n⚠️  Couldn't copy to clipboard automatically.")
        print(f"\n📄 Open this file to copy: meeting_{meeting_id}_reddit_comment.md")

    print("\n📋 PREVIEW:")
    print("=" * 60)
    print(reddit_comment)
    print("=" * 60)

    print(f"\n✅ Summary saved to: meeting_{meeting_id}_reddit_comment.md")
    print("   Ready to post to r/losangeles daily discussion thread!")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
