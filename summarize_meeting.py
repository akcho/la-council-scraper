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

IMPORTANT: Do NOT start your summary with meta-commentary about the meeting being "mostly ceremonial" or "primarily routine". Start directly with the KEY DECISIONS section. Let the content speak for itself."""

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
        # Use prompt caching to reduce costs and avoid rate limits
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # Latest Claude model
            max_tokens=800,  # Shorter for comment format
            temperature=0.3,  # Lower temp for more factual output
            system=[
                {
                    "type": "text",
                    "text": SUMMARIZATION_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"TRANSCRIPT:\n\n{transcript}",
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                }
            ]
        )

        summary = message.content[0].text
        print(f"✅ Got summary: {len(summary)} characters")

        return summary

    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        raise


def format_summary_for_reddit(meeting_info: dict, summary: str, site_url: str = None) -> str:
    """Format the summary as a Reddit comment for daily discussion thread."""

    title = meeting_info.get('title', 'LA City Council Meeting')
    date = meeting_info.get('date', 'Unknown Date')
    video_url = meeting_info.get('videoUrl', '')
    meeting_id = meeting_info.get('id', '')

    # Build links section
    links = []

    # Add meeting page link if site_url is configured
    if site_url and meeting_id:
        meeting_page_url = f"{site_url}/meetings/{meeting_id}.html"
        links.append(f"📋 [View Details]({meeting_page_url})")

    # Add video link
    if video_url:
        links.append(f"📺 [Watch Meeting]({video_url})")

    # Add official agenda link
    if meeting_id:
        links.append(f"📄 [Official Agenda](https://lacity.primegov.com/Portal/Meeting?meetingTemplateId={meeting_id})")

    links_text = " | ".join(links)

    comment = f"""**{title} - {date}**

{summary}

{links_text}

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

    # Load site config to get site URL
    site_url = None
    try:
        with open('site_config.json', 'r') as f:
            config = json.load(f)
            site_url = config.get('site_url', '')
            if site_url:
                print(f"📍 Site URL: {site_url}\n")
    except FileNotFoundError:
        print("ℹ️  No site_config.json found (meeting page link will be omitted)\n")

    # Load meeting data
    try:
        with open('recent_meetings.json', 'r') as f:
            meetings = json.load(f)
    except FileNotFoundError:
        print("❌ Run fetch_meetings.py first!")
        return

    # Find the most recent meeting with a video AND transcript
    meeting = None
    transcript_file = None

    for m in meetings:
        if m.get('videoUrl'):  # Has video
            meeting_id = m['id']
            candidate_file = f"meeting_{meeting_id}_transcript.txt"

            # Check if transcript exists
            if os.path.exists(candidate_file):
                meeting = m
                transcript_file = candidate_file
                break

    if not meeting or not transcript_file:
        print("❌ No meetings with transcripts found!")
        print("   Make sure get_transcripts.py ran successfully.")
        return

    meeting_id = meeting['id']

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
    reddit_comment = format_summary_for_reddit(meeting, summary, site_url)

    # Save both
    summary_file = f"meeting_{meeting_id}_summary.txt"
    reddit_file = f"meeting_{meeting_id}_reddit_comment.md"

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    with open(reddit_file, 'w', encoding='utf-8') as f:
        f.write(reddit_comment)

    print("\n💾 Saved:")
    print(f"   - {summary_file}")
    print(f"   - {reddit_file}")

    print("\n📋 PREVIEW:")
    print("=" * 60)
    print(reddit_comment)
    print("=" * 60)

    # Open the markdown file in default editor
    print(f"\n✅ Summary ready!")
    print(f"\n📝 Opening {reddit_file} in your editor...")
    print("   Copy the markdown from the file to preserve formatting.\n")

    try:
        import subprocess
        # Open in default markdown editor (VS Code, TextEdit, etc.)
        subprocess.run(['open', reddit_file])
    except:
        print(f"⚠️  Couldn't open automatically. Manual path:")
        print(f"   {os.path.abspath(reddit_file)}")

    print("\n" + "=" * 60)
    print("Next steps:")
    print("1. Copy content from the opened file")
    print("2. Go to r/losangeles daily discussion thread")
    print("3. Paste into Reddit comment (Cmd+V)")
    print("4. Click 'Comment'")
    print("=" * 60)


if __name__ == "__main__":
    main()
