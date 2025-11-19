#!/usr/bin/env python3
"""
Static site generator for LA Council meeting pages.

Reads parsed agenda JSON files and generates mobile-first HTML pages.
"""

import json
import os
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

def format_meeting_date(date_str):
    """Format meeting date from ISO format to readable format."""
    if not date_str:
        return "Date TBD"

    try:
        # Try parsing ISO format
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y at %I:%M %p")
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
        "Items for which Public Hearings Have Been Held": "Public Hearing Items",
        "Closed Session": "Closed Session Items",
        "Commendatory Resolutions, Introductions and Presentations": "Commendations and Presentations",
        "Public Testimony of Non-agenda Items Within Jurisdiction of Council": "Public Comment",
        "Multiple Agenda Item Comment": "General Public Comment",
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

    # Prepare template context
    context = {
        'meeting_id': meeting_id,
        'template_id': agenda.get('template_id'),
        'portal_url': agenda.get('portal_url', ''),
        'sections': agenda.get('sections', []),
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Add analytics if configured
    if config.get('analytics', {}).get('domain'):
        context['analytics_domain'] = config['analytics']['domain']

    # Add metadata if available
    if metadata:
        context['meeting_title'] = metadata.get('name', f'City Council Meeting {meeting_id}')
        # Try dateTime first, then meetingDate
        date_value = metadata.get('dateTime') or metadata.get('meetingDate')
        context['meeting_date'] = format_meeting_date(date_value)

        # Look for video URL in metadata first, then in agenda
        video_url = metadata.get('videoUrl') or metadata.get('video_url') or agenda.get('video_url')
        if video_url:
            context['video_url'] = video_url
    else:
        # Fallback if metadata not found
        context['meeting_title'] = f'City Council Meeting {meeting_id}'
        context['meeting_date'] = 'Date TBD'
        # Check for video in agenda even without metadata
        video_url = agenda.get('video_url')
        if video_url:
            context['video_url'] = video_url

    # Load video summary if available
    video_summary_data = load_video_summary(meeting_id)
    if video_summary_data:
        context['video_summary'] = video_summary_data.get('summary')

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

    context = {
        'meetings': meetings_data,
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

            meetings_data.append({
                'meeting_id': meeting_id,
                'title': metadata.get('name', f'City Council Meeting {meeting_id}') if metadata else f'City Council Meeting {meeting_id}',
                'date': format_meeting_date(metadata.get('dateTime') or metadata.get('meetingDate')) if metadata else 'Date TBD',
                'items_count': items_count
            })

        except Exception as e:
            print(f"✗ Failed to generate page for meeting {meeting_id}: {e}")
            failed.append(meeting_id)

    # Generate index page
    if meetings_data:
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
