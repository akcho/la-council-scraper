#!/usr/bin/env python3
"""
Static site generator for LA Council meeting pages.

Reads parsed agenda JSON files and generates mobile-first HTML pages.
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Paths
AGENDAS_DIR = Path("data/agendas")
TEMPLATES_DIR = Path("templates")
OUTPUT_DIR = Path("site/meetings")
VIDEO_SUMMARIES_DIR = Path("data/video_summaries")
RECENT_MEETINGS_FILE = Path("recent_meetings.json")
SITE_CONFIG_FILE = Path("site_config.json")

def markdown_to_html(text):
    """
    Convert simple markdown formatting to HTML.
    Handles **bold**, *italic*, ## headers, and preserves line breaks.
    """
    if not text:
        return text

    # Convert ## headers to <strong> (for section headers)
    text = re.sub(r'^## (.+)$', r'<strong>\1</strong>', text, flags=re.MULTILINE)

    # Convert **bold** to <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Convert *italic* to <em> (but not if it's already part of **)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

    return text

def load_site_config():
    """Load site configuration."""
    if not SITE_CONFIG_FILE.exists():
        return {}

    with open(SITE_CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_agenda(meeting_id):
    """Load parsed agenda JSON for a meeting."""
    agenda_file = AGENDAS_DIR / f"agenda_{meeting_id}.json"
    if not agenda_file.exists():
        raise FileNotFoundError(f"Agenda file not found: {agenda_file}")

    with open(agenda_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_meeting_metadata(meeting_id):
    """Load meeting metadata from recent_meetings.json."""
    if not RECENT_MEETINGS_FILE.exists():
        return None

    try:
        with open(RECENT_MEETINGS_FILE, 'r', encoding='utf-8') as f:
            meetings = json.load(f)

        # Find the meeting by ID
        for meeting in meetings:
            if meeting.get('id') == meeting_id:
                return meeting
    except Exception as e:
        print(f"Warning: Failed to load meeting metadata: {e}")

    return None

def load_video_summary(meeting_id):
    """Load video summary for a meeting if available."""
    summary_file = VIDEO_SUMMARIES_DIR / f"meeting_{meeting_id}_summary.json"
    if not summary_file.exists():
        return None

    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load video summary for meeting {meeting_id}: {e}")
        return None

def load_council_file(council_file_number):
    """Load council file data including AI summaries."""
    council_file_path = Path("data/councilfiles") / f"{council_file_number}.json"
    if not council_file_path.exists():
        return None

    try:
        with open(council_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load council file {council_file_number}: {e}")
        return None

def get_brief_summary(council_file_data):
    """Extract a brief, user-friendly summary from council file data."""
    if not council_file_data:
        return None

    # Look for attachments with summaries
    attachments = council_file_data.get('attachments', [])
    for attachment in attachments:
        if attachment.get('has_summary') and attachment.get('summary'):
            summary_text = attachment['summary']
            # Extract just the "What is Being Proposed?" section
            lines = summary_text.split('\n')
            for i, line in enumerate(lines):
                if 'What is Being Proposed?' in line or 'What is this?' in line:
                    # Get the next few lines (skip the header line)
                    start_idx = i + 1
                    brief_lines = []
                    for j in range(start_idx, min(start_idx + 10, len(lines))):
                        line_text = lines[j].strip()
                        # Stop at next section header or empty markdown header
                        if line_text.startswith('##') or (line_text == '' and brief_lines):
                            break
                        if line_text and not line_text.startswith('#'):
                            brief_lines.append(line_text)
                    if brief_lines:
                        return ' '.join(brief_lines)
            # Fallback: just grab first few sentences, skipping markdown headers
            if summary_text:
                # Remove all markdown headers (lines starting with #)
                clean_lines = []
                for line in summary_text.split('\n'):
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#'):
                        clean_lines.append(stripped)

                clean_text = ' '.join(clean_lines)
                sentences = clean_text.split('. ')
                return '. '.join(sentences[:2]) + '.' if len(sentences) >= 2 else sentences[0]

    return None

def format_meeting_date(date_str):
    """Format meeting date from ISO format to readable format (date only, no time)."""
    if not date_str:
        return "Date TBD"

    try:
        # Try parsing ISO format
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y")
    except:
        return date_str

def improve_section_title(title):
    """
    Convert bureaucratic section titles to clearer, more readable titles.

    Args:
        title: Original section title from agenda

    Returns:
        Improved, more readable title
    """
    # Mapping of common bureaucratic titles to clearer alternatives
    title_improvements = {
        "Items Noticed for Public Hearing": "Scheduled hearings",
        "Items for which Public Hearings Have Been Held": "Completed hearings",
        "Items for which Public Hearings Have Not Been Held - (10 Votes Required for Consideration)": "No hearings held (requires 10 votes)",
        "Closed Session": "Closed sessions",
        "Commendatory Resolutions, Introductions and Presentations": "Commendations and presentations",
        "Public Testimony of Non-agenda Items Within Jurisdiction of Council": "Public comments",
        "Multiple Agenda Item Comment": "General public comments",
    }

    # Return improved title if available, otherwise return original
    return title_improvements.get(title, title)

def generate_meeting_page(meeting_id):
    """Generate HTML page for a single meeting."""

    # Load configuration
    config = load_site_config()

    # Load agenda data
    agenda = load_agenda(meeting_id)

    # Load meeting metadata
    metadata = load_meeting_metadata(meeting_id)

    # Enrich agenda items with AI summaries
    sections = agenda.get('sections', [])
    for section in sections:
        for item in section.get('items', []):
            council_file = item.get('council_file')
            if council_file:
                council_file_data = load_council_file(council_file)
                if council_file_data:
                    brief_summary = get_brief_summary(council_file_data)
                    if brief_summary:
                        # Convert markdown to HTML for display
                        item['ai_summary'] = markdown_to_html(brief_summary)

    # Prepare template context
    context = {
        'meeting_id': meeting_id,
        'template_id': agenda.get('template_id'),
        'portal_url': agenda.get('portal_url', ''),
        'sections': sections,
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Add analytics if configured
    if config.get('analytics', {}).get('domain'):
        context['analytics_domain'] = config['analytics']['domain']

    # Add metadata if available
    if metadata:
        # Use committee name as title if meeting name is empty
        meeting_title = metadata.get('name') or metadata.get('committeeName') or 'City Council Meeting'
        context['meeting_title'] = meeting_title
        # Try dateTime first, then meetingDate
        date_value = metadata.get('dateTime') or metadata.get('meetingDate')
        context['meeting_date'] = format_meeting_date(date_value)

        # Look for video URL in metadata first, then in agenda
        video_url = metadata.get('videoUrl') or metadata.get('video_url') or agenda.get('video_url')
        if video_url:
            context['video_url'] = video_url
    else:
        # Fallback if metadata not found - try to get date from parsed agenda
        context['meeting_title'] = 'City Council Meeting'

        # Try to get meeting datetime from parsed agenda
        meeting_datetime = agenda.get('meeting_datetime')
        if meeting_datetime:
            context['meeting_date'] = format_meeting_date(meeting_datetime)
        else:
            context['meeting_date'] = 'Date TBD'

        # Check for video in agenda even without metadata
        video_url = agenda.get('video_url')
        if video_url:
            context['video_url'] = video_url

    # Load video summary if available
    video_summary_data = load_video_summary(meeting_id)
    if video_summary_data:
        # Convert markdown in video summary to HTML
        raw_summary = video_summary_data.get('summary', '')

        # Remove the introductory sentence (first paragraph before the first ##)
        # These typically start with "This was mostly..." or similar
        lines = raw_summary.split('\n')
        filtered_lines = []
        found_first_header = False

        for line in lines:
            # Skip lines before the first ## header
            if line.strip().startswith('##'):
                found_first_header = True

            if found_first_header:
                filtered_lines.append(line)

        # If we found headers, use filtered version; otherwise use original
        if filtered_lines:
            raw_summary = '\n'.join(filtered_lines)

        context['video_summary'] = markdown_to_html(raw_summary)

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Add custom filters
    env.filters['improve_section_title'] = improve_section_title

    # Load template
    template = env.get_template('meeting.html')

    # Render HTML
    html = template.render(**context)

    # Write output file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{meeting_id}.html"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Generated: {output_file}")
    return output_file

def generate_index_page(meetings_data):
    """Generate the index page with list of all meetings."""
    config = load_site_config()

    # Extract unique committees for filter tabs
    committees = {}
    for meeting in meetings_data:
        cid = meeting.get('committee_id', 1)
        cname = meeting.get('committee_name', 'City Council Meeting')
        if cid not in committees:
            committees[cid] = cname

    # Sort committees: City Council (1) first, then alphabetically
    sorted_committees = sorted(
        committees.items(),
        key=lambda x: (0 if x[0] == 1 else 1, x[1])
    )

    context = {
        'meetings': meetings_data,
        'committees': [{'id': cid, 'name': cname} for cid, cname in sorted_committees],
        'generated_at': datetime.now().strftime("%Y-%m-%d"),
    }

    # Add analytics if configured
    if config.get('analytics', {}).get('domain'):
        context['analytics_domain'] = config['analytics']['domain']

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Load template
    template = env.get_template('index.html')

    # Render HTML
    html = template.render(**context)

    # Write output file
    output_dir = Path("site")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "index.html"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Generated: {output_file}")
    return output_file

def generate_all_meetings():
    """Generate HTML pages for all parsed agendas."""

    if not AGENDAS_DIR.exists():
        print(f"Error: Agendas directory not found: {AGENDAS_DIR}")
        return

    # Find all agenda JSON files
    agenda_files = sorted(AGENDAS_DIR.glob("agenda_*.json"), reverse=True)

    if not agenda_files:
        print(f"No agenda files found in {AGENDAS_DIR}")
        return

    print(f"Found {len(agenda_files)} agenda file(s)")
    print()

    generated = []
    failed = []
    meetings_data = []

    for agenda_file in agenda_files:
        # Extract meeting ID from filename
        # Format: agenda_17432.json
        filename = agenda_file.stem
        meeting_id = int(filename.replace('agenda_', ''))

        try:
            output_file = generate_meeting_page(meeting_id)
            generated.append(output_file)

            # Collect meeting data for index page
            metadata = load_meeting_metadata(meeting_id)
            agenda = load_agenda(meeting_id)

            # Count total agenda items
            items_count = sum(len(section.get('items', [])) for section in agenda.get('sections', []))

            # Determine date - try metadata first, then parsed agenda
            if metadata:
                date_value = metadata.get('dateTime') or metadata.get('meetingDate')
                meeting_date = format_meeting_date(date_value)
            else:
                # Fallback to agenda's meeting_datetime
                meeting_datetime = agenda.get('meeting_datetime')
                meeting_date = format_meeting_date(meeting_datetime) if meeting_datetime else 'Date TBD'

            # Get committee info from metadata
            committee_name = None
            committee_id = None
            if metadata:
                committee_name = metadata.get('committeeName')
                committee_id = metadata.get('committeeId')

            # Use committee name as title if meeting name is empty
            meeting_title = None
            if metadata:
                meeting_title = metadata.get('name') or committee_name
            meeting_title = meeting_title or 'City Council Meeting'

            meetings_data.append({
                'meeting_id': meeting_id,
                'title': meeting_title,
                'date': meeting_date,
                'items_count': items_count,
                'committee_name': committee_name or 'City Council Meeting',
                'committee_id': committee_id or 1
            })

        except Exception as e:
            print(f"✗ Failed to generate page for meeting {meeting_id}: {e}")
            failed.append(meeting_id)

    # Generate index page
    if meetings_data:
        # Sort meetings by date (most recent first)
        # Parse the formatted dates back to compare them
        def parse_meeting_date(meeting):
            try:
                date_str = meeting['date']
                # Parse "November 07, 2025" format (date only, no time)
                dt = datetime.strptime(date_str, "%B %d, %Y")
                return dt
            except:
                # If parsing fails, put it at the end
                return datetime.min

        meetings_data.sort(key=parse_meeting_date, reverse=True)

        print()
        generate_index_page(meetings_data)

    # Summary
    print()
    print(f"Generated {len(generated)} meeting page(s)")

    if failed:
        print(f"Failed: {len(failed)} page(s)")
        print(f"  Meeting IDs: {', '.join(map(str, failed))}")

    if generated:
        print()
        print("Pages saved to:")
        print(f"  {OUTPUT_DIR.absolute()}")

def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        # Generate specific meeting
        meeting_id = int(sys.argv[1])
        try:
            output_file = generate_meeting_page(meeting_id)
            print()
            print(f"View at: file://{output_file.absolute()}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Generate all meetings
        generate_all_meetings()

if __name__ == "__main__":
    main()
