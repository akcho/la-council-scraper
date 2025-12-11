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

SUMMARIZATION_PROMPT = """You are a local government reporter covering Los Angeles City Council for engaged residents. Write a news-style summary that explains what happened and why it matters.

IMPORTANT: The transcript may include intro segments from "LA This Week" or other pre-roll content before the actual City Council meeting begins. Skip any such intro material and focus on the actual City Council meeting proceedings that follow. The meeting typically starts with roll call and "Good morning and welcome to the regularly scheduled meeting..."

Write in a clear, narrative style - like a news article, not bullet points. Use paragraphs and complete sentences.

YOU MUST PROVIDE TWO OUTPUTS, SEPARATED BY THE DELIMITER "---NEWSLETTER---":

=== PART 1: FULL ARTICLE (before the delimiter) ===

STRUCTURE YOUR SUMMARY AS FOLLOWS:

## What Happened
2-3 paragraphs covering the major actions taken. For each significant vote or decision:
- What was decided and the vote count
- Who voted against (use full correct names - verify spelling from context)
- The specific policy details: dollar thresholds, timelines, notice requirements, who it applies to
- Context: why this came up now, what problem it's trying to solve

## The Debate
1-2 paragraphs on the most contentious or interesting discussions:
- Present BOTH sides fairly: what supporters say AND what critics say
- Which council members took strong positions and what did they say?
- Include direct quotes when they're revealing or memorable
- What did public commenters say? Highlight specific stories or perspectives

## What It Means
1-2 paragraphs on implications:
- How will this affect LA residents? Be specific about who's impacted
- What happens next? (implementation timeline, upcoming votes, potential legal challenges)
- Unanswered questions or things to watch

GUIDELINES FOR FULL ARTICLE:
- Around 500 words total
- Write like a reporter: factual, specific, balanced
- Use names: "Council Member Hernandez argued..." not "One member said..."
- CRITICAL: Include specific numbers - dollar amounts, value thresholds, vote counts, dates, percentages, notice periods
- For legislation (AB/SB bills): explain what the law actually does, not just what critics or supporters claim
- Explain jargon naturally: "the RSO (the city's rent control law)" on first use
- When quoting, use the most substantive or revealing quotes, not pleasantries

=== PART 2: NEWSLETTER BLURB (after the delimiter) ===

Write a 75-100 word condensed summary for a weekly email newsletter. Format:
- 1 sentence on the key action/decision (include vote count if significant)
- 1-2 sentences on why it matters / who's affected
- Keep it scannable - readers will see 3-4 meeting summaries in one email

Do NOT include headers, bullets, or markdown formatting in the newsletter blurb. Just plain paragraph text.

=== REFERENCE INFO (applies to both outputs) ===

Current council members (2025): Eunisses Hernandez (D1), Adrin Nazarian (D2), Bob Blumenfield (D3), Nithya Raman (D4), Katy Yaroslavsky (D5), Imelda Padilla (D6), Monica Rodriguez (D7), Marqueece Harris-Dawson (D8, Council President), Curren D. Price Jr. (D9), Heather Hutt (D10), Traci Park (D11), John Lee (D12), Hugo Soto-Martinez (D13), Ysabel Jurado (D14), Tim McOsker (D15)

TECHNICAL TERMS TO EXPLAIN (spell out on first use):
- RSO: Rent Stabilization Ordinance (LA's rent control law covering ~650,000 units)
- CUP: Conditional Use Permit (discretionary approval requiring public hearing)
- CEQA: California Environmental Quality Act (environmental review requirement)
- CF/Council File: the official record number for legislation
- AB/SB: Assembly Bill / Senate Bill (state legislation)
- CAO: City Administrative Officer (the city's chief financial advisor)
- CLA: Chief Legislative Analyst (provides policy analysis to Council)
- DWP/LADWP: Department of Water and Power
- LAPD: Los Angeles Police Department
- LAFD: Los Angeles Fire Department
- LAHD: LA Housing Department
- HCID/HCIDLA: Housing and Community Investment Department
- BOE: Bureau of Engineering
- BSS: Bureau of Street Services
- CD: Council District (e.g., CD4 = Council District 4)
- PLUM: Planning and Land Use Management Committee
- MOU: Memorandum of Understanding (labor agreement)

ABSOLUTELY DO NOT:
- Start with "This meeting..." or any meta-commentary about the transcript
- Use words like: ceremonial, routine, primarily, mostly
- Write bullet points (use flowing paragraphs instead)
- Editorialize or inject opinion - stick to what was said and decided
- Summarize procedural items unless they're actually newsworthy
- Accept one side's framing without presenting the other side's perspective

Start the full article directly with "## What Happened" - no preamble."""

def summarize_with_claude(transcript: str, api_key: str = None) -> tuple[str, str]:
    """
    Summarize meeting transcript using Claude API.

    Args:
        transcript: Full meeting transcript text
        api_key: Anthropic API key (or reads from ANTHROPIC_API_KEY env var)

    Returns:
        Tuple of (full_summary, newsletter_blurb)
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
            max_tokens=1500,  # ~500 word article + ~100 word newsletter
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

        full_response = message.content[0].text
        print(f"✅ Got response: {len(full_response)} characters")

        # Parse the two outputs
        if "---NEWSLETTER---" in full_response:
            parts = full_response.split("---NEWSLETTER---", 1)
            full_summary = parts[0].strip()
            newsletter_blurb = parts[1].strip()
        else:
            # Fallback if delimiter not found
            print("⚠️  Newsletter delimiter not found, using full summary")
            full_summary = full_response
            newsletter_blurb = ""

        print(f"   Full summary: {len(full_summary)} chars")
        print(f"   Newsletter blurb: {len(newsletter_blurb)} chars")

        return full_summary, newsletter_blurb

    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        raise


def format_newsletter_blurb(meeting_info: dict, blurb: str, site_url: str = None) -> str:
    """Format newsletter blurb with meeting header and link."""

    title = meeting_info.get('title', '')
    date = meeting_info.get('date', 'Unknown Date')
    meeting_id = meeting_info.get('id', '')

    # Only include committee name if it's not City Council
    if title and 'City Council' not in title:
        header = f"**{title} - {date}**"
    else:
        header = f"**{date}**"

    # Build the "Read more" link
    read_more = ""
    if site_url and meeting_id:
        meeting_page_url = f"{site_url}/meetings/{meeting_id}.html"
        read_more = f" [Read more →]({meeting_page_url})"

    return f"{header}\n\n{blurb}{read_more}"


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

{links_text}"""

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
    summary, newsletter_blurb = summarize_with_claude(transcript, api_key)

    print("\n" + "=" * 60)
    print("FULL SUMMARY")
    print("=" * 60 + "\n")
    print(summary)
    print("\n" + "=" * 60)

    if newsletter_blurb:
        print("\nNEWSLETTER BLURB")
        print("=" * 60 + "\n")
        print(newsletter_blurb)
        print("\n" + "=" * 60)

    # Format for Reddit daily discussion comment
    reddit_comment = format_summary_for_reddit(meeting, summary, site_url)

    # Save all outputs
    summary_file = f"meeting_{meeting_id}_summary.txt"
    reddit_file = f"meeting_{meeting_id}_reddit_comment.md"
    newsletter_file = f"meeting_{meeting_id}_newsletter.txt"

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    with open(reddit_file, 'w', encoding='utf-8') as f:
        f.write(reddit_comment)

    if newsletter_blurb:
        formatted_newsletter = format_newsletter_blurb(meeting, newsletter_blurb, site_url)
        with open(newsletter_file, 'w', encoding='utf-8') as f:
            f.write(formatted_newsletter)

    print("\n💾 Saved:")
    print(f"   - {summary_file}")
    print(f"   - {reddit_file}")
    if newsletter_blurb:
        print(f"   - {newsletter_file}")

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
