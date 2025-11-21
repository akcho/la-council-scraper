#!/usr/bin/env python3
"""
Generate HTML pages for council files showing timeline and AI summaries.
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def load_meeting_metadata():
    """Load meeting metadata from recent_meetings.json and agendas."""
    meetings = {}

    # Try to load from recent_meetings.json first
    recent_meetings_file = Path("recent_meetings.json")
    if recent_meetings_file.exists():
        try:
            with open(recent_meetings_file, 'r', encoding='utf-8') as f:
                meetings_list = json.load(f)
                for meeting in meetings_list:
                    meeting_id = meeting.get('id')
                    if meeting_id:
                        meetings[meeting_id] = {
                            'title': meeting.get('name', 'City Council Meeting'),
                            'date': meeting.get('dateTime') or meeting.get('meetingDate', ''),
                        }
        except Exception as e:
            print(f"Warning: Could not load recent_meetings.json: {e}")

    # Load from agenda files as fallback/supplement
    agendas_dir = Path("data/agendas")
    if agendas_dir.exists():
        for agenda_file in agendas_dir.glob("agenda_*.json"):
            try:
                with open(agenda_file, 'r', encoding='utf-8') as f:
                    agenda = json.load(f)
                    meeting_id = agenda.get('meeting_id')
                    if meeting_id and meeting_id not in meetings:
                        meetings[meeting_id] = {
                            'title': 'City Council Meeting',
                            'date': agenda.get('meeting_datetime', ''),
                        }
            except Exception as e:
                print(f"Warning: Could not load {agenda_file}: {e}")

    return meetings


def markdown_to_html(text: str) -> str:
    """
    Convert simple markdown formatting to HTML.
    Handles **bold**, *italic*, and preserves line breaks.
    """
    if not text:
        return text

    # Convert **bold** to <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Convert *italic* to <em> (but not if it's already part of **)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

    return text


def format_date(date_str: str) -> str:
    """Format ISO date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y')
    except:
        return date_str


def extract_brief_summary(file_data: Dict[str, Any]) -> str:
    """
    Extract a brief, human-readable summary from AI summaries.
    Falls back to a shortened title if no summaries are available.
    """
    attachments = file_data.get('attachments', [])

    # Find first attachment with a summary
    for attachment in attachments:
        if attachment.get('has_summary', False):
            summary_text = attachment.get('summary', '')
            if summary_text:
                # Extract the first ## section after the title
                lines = summary_text.strip().split('\n')
                current_paragraph = []
                in_first_section = False

                for line in lines:
                    line = line.strip()
                    if not line:
                        if in_first_section and current_paragraph:
                            # Found end of first paragraph
                            break
                        continue

                    if line.startswith('# '):
                        # Skip main title
                        continue
                    elif line.startswith('## '):
                        # Found first section heading - skip it and start collecting content
                        in_first_section = True
                        continue
                    elif in_first_section:
                        # Collect content from first section
                        if line.startswith('- '):
                            current_paragraph.append(line[2:])
                        else:
                            current_paragraph.append(line)

                if current_paragraph:
                    # Return first 1-2 sentences (up to ~200 chars)
                    text = ' '.join(current_paragraph)
                    # Simple sentence splitting
                    sentences = text.split('. ')
                    result = sentences[0]
                    if len(result) < 150 and len(sentences) > 1:
                        result += '. ' + sentences[1]
                    if not result.endswith('.'):
                        result += '.'
                    return result

    # Fallback to shortened title (first sentence or 200 chars)
    title = file_data.get('title', '')
    # Try to get first sentence
    if '; ' in title:
        # Split on semicolon for bureaucratic titles
        return title.split('; ')[0] + '.'
    elif len(title) > 200:
        # Truncate to 200 chars
        return title[:200] + '...'
    else:
        return title


def generate_council_file_page(file_data: Dict[str, Any], output_dir: Path, meetings_metadata: Dict[int, Dict[str, Any]]) -> None:
    """Generate HTML page for a single council file."""

    council_file = file_data['council_file']
    title = file_data['title']
    brief_summary = extract_brief_summary(file_data)
    has_ai_summary = any(a.get('has_summary', False) for a in file_data.get('attachments', []))
    district = file_data.get('district', 'Unknown')
    first_seen = format_date(file_data['first_seen'])
    last_seen = format_date(file_data['last_seen'])

    appearances = file_data.get('appearances', [])
    attachments = file_data.get('attachments', [])
    stats = file_data.get('stats', {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Council File {council_file} - LA Council Tracker</title>
    <meta name="description" content="Timeline and details for Council File {council_file}: {title[:150]}">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background: #f5f5f5;
            padding-bottom: 2rem;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 0 1rem;
        }}

        header {{
            background: #fff;
            border-bottom: 1px solid #e0e0e0;
            padding: 1.5rem 0;
            margin-bottom: 1.5rem;
        }}

        .breadcrumb {{
            font-size: 0.875rem;
            color: #666;
            margin-bottom: 0.75rem;
        }}

        .breadcrumb a {{
            color: #0066cc;
            text-decoration: none;
        }}

        .breadcrumb a:hover {{
            text-decoration: underline;
        }}

        h1 {{
            font-size: 1.25rem;
            font-weight: 500;
            line-height: 1.4;
            margin-bottom: 1rem;
            color: #1a1a1a;
        }}

        .official-title {{
            font-size: 0.875rem;
            color: #666;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e0e0e0;
        }}

        .official-title-label {{
            font-weight: 600;
            display: block;
            margin-bottom: 0.5rem;
        }}

        .file-number {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #0066cc;
            margin-bottom: 0.75rem;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
            padding: 1rem;
            background: #f9f9f9;
            border-radius: 8px;
        }}

        .meta-item {{
            font-size: 0.875rem;
        }}

        .meta-label {{
            font-weight: 600;
            color: #666;
            display: block;
            margin-bottom: 0.25rem;
        }}

        .meta-value {{
            color: #1a1a1a;
        }}

        .section {{
            margin-bottom: 2rem;
        }}

        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 1rem;
            padding-left: 0.75rem;
            border-left: 3px solid #0066cc;
        }}

        .timeline {{
            position: relative;
            padding-left: 2rem;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 0.5rem;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #e0e0e0;
        }}

        .timeline-item {{
            position: relative;
            margin-bottom: 2rem;
        }}

        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -1.65rem;
            top: 0.5rem;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #0066cc;
            border: 3px solid #fff;
            box-shadow: 0 0 0 2px #e0e0e0;
        }}

        .timeline-card {{
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            text-decoration: none;
            color: inherit;
            display: block;
            transition: box-shadow 0.2s, border-color 0.2s, transform 0.2s;
        }}

        .timeline-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-color: #0066cc;
            transform: translateY(-2px);
        }}

        .timeline-date {{
            font-size: 0.875rem;
            font-weight: 600;
            color: #0066cc;
            margin-bottom: 0.5rem;
        }}

        .timeline-meeting-title {{
            font-size: 1rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 0.75rem;
        }}

        .timeline-summary {{
            font-size: 0.875rem;
            color: #555;
            line-height: 1.5;
        }}

        .timeline-recommendation {{
            margin-top: 0.75rem;
            padding: 0.75rem;
            background: #f9f9f9;
            border-radius: 4px;
            font-size: 0.875rem;
            color: #333;
            line-height: 1.5;
        }}

        .attachments {{
            margin-top: 1.5rem;
        }}

        .attachments-title {{
            font-size: 1rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 0.75rem;
        }}

        .attachment {{
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        .attachment-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 1rem;
        }}

        .attachment-title {{
            font-size: 0.9375rem;
            font-weight: 600;
            color: #1a1a1a;
            flex: 1;
        }}

        .attachment-badge {{
            background: #e8f4f8;
            color: #0066cc;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .summary {{
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid #e0e0e0;
        }}

        .summary h4 {{
            font-size: 1rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 0.5rem;
        }}

        .summary p {{
            color: #333;
            margin-bottom: 0.75rem;
            line-height: 1.6;
        }}

        .summary h5 {{
            font-size: 0.9375rem;
            font-weight: 600;
            color: #1a1a1a;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }}

        .no-summary {{
            color: #666;
            font-style: italic;
            font-size: 0.875rem;
        }}

        .meeting-link {{
            display: inline-block;
            margin-top: 0.5rem;
            font-size: 0.875rem;
            color: #0066cc;
            text-decoration: none;
        }}

        .meeting-link:hover {{
            text-decoration: underline;
        }}

        @media (max-width: 640px) {{
            h1 {{
                font-size: 1.25rem;
            }}

            .file-number {{
                font-size: 1rem;
            }}

            .meta-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .no-summaries {{
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
        }}

        .no-summaries summary {{
            cursor: pointer;
            font-size: 0.875rem;
            color: #666;
            font-weight: 600;
        }}

        .no-summaries ul {{
            margin-top: 0.75rem;
            padding-left: 1.5rem;
        }}

        .no-summaries li {{
            font-size: 0.875rem;
            color: #666;
            margin-bottom: 0.25rem;
        }}

        .doc-link {{
            color: #0066cc;
            text-decoration: none;
        }}

        .doc-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="breadcrumb">
                <a href="../index.html">Home</a> /
                <a href="index.html">Council Files</a> /
                {council_file}
            </div>
            <div class="file-number">{council_file}</div>
            <h1>{markdown_to_html(brief_summary)}</h1>
            <div class="meta-grid">
                <div class="meta-item">
                    <span class="meta-label">District</span>
                    <span class="meta-value">{district}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">First Seen</span>
                    <span class="meta-value">{first_seen}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Last Seen</span>
                    <span class="meta-value">{last_seen}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Appearances</span>
                    <span class="meta-value">{stats.get('total_appearances', 0)} meeting(s)</span>
                </div>
            </div>
            {f'''<div class="official-title">
                <span class="official-title-label">Official Title:</span>
                {title}
            </div>''' if has_ai_summary else ''}
        </div>
    </header>

    <main class="container">
"""

    # Timeline section
    if appearances:
        html += """        <section class="section">
            <h2 class="section-title">Timeline</h2>
            <div class="timeline">
"""

        for appearance in appearances:
            date = format_date(appearance['date'])
            meeting_id = appearance.get('meeting_id', '')

            # Get meeting metadata
            meeting_info = meetings_metadata.get(meeting_id, {})
            meeting_title = meeting_info.get('title', 'City Council Meeting')

            html += f"""                <div class="timeline-item">
"""

            if meeting_id:
                html += f"""                    <a href="../meetings/{meeting_id}.html" class="timeline-card">
                        <div class="timeline-date">{date}</div>
                        <div class="timeline-meeting-title">{meeting_title}</div>
                    </a>
"""
            else:
                html += f"""                    <div class="timeline-card">
                        <div class="timeline-date">{date}</div>
                        <div class="timeline-meeting-title">{meeting_title}</div>
                    </div>
"""

            html += """                </div>
"""

        html += """            </div>
        </section>
"""

    # Attachments section - separate summaries from non-summaries
    if attachments:
        # Split attachments into those with and without summaries
        with_summaries = [a for a in attachments if a.get('has_summary', False)]
        without_summaries = [a for a in attachments if not a.get('has_summary', False)]

        if with_summaries:
            html += """        <section class="section">
            <h2 class="section-title">Related Documents</h2>
"""

            for attachment in with_summaries:
                title_text = attachment.get('text', 'Untitled Document')
                summary_text = attachment.get('summary', '')
                url = attachment.get('url', '')

                html += f"""            <div class="attachment">
                <div class="attachment-header">
                    <div class="attachment-title">"""

                if url:
                    full_url = f"https://lacity.primegov.com{url}"
                    html += f"""<a href="{full_url}" class="doc-link" target="_blank">{title_text}</a>"""
                else:
                    html += title_text

                html += """</div>
                </div>
"""

                # Parse markdown-style summary
                lines = summary_text.strip().split('\n')
                html += """                <div class="summary">
"""

                current_section = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith('# '):
                        # Skip main title
                        continue
                    elif line.startswith('## '):
                        # Section heading
                        if current_section:
                            html += '<p>' + markdown_to_html(' '.join(current_section)) + '</p>\n'
                            current_section = []
                        html += f'<h5>{line[3:]}</h5>\n'
                    elif line.startswith('- '):
                        # Bullet point - treat as regular text
                        current_section.append(line[2:])
                    else:
                        current_section.append(line)

                if current_section:
                    html += '<p>' + markdown_to_html(' '.join(current_section)) + '</p>\n'

                html += """                </div>
            </div>
"""

            html += """        </section>
"""

        # Show documents without summaries in a collapsed section
        if without_summaries:
            html += f"""        <section class="section">
            <details class="no-summaries">
                <summary>{len(without_summaries)} additional document(s) without AI summaries</summary>
                <ul>
"""
            for attachment in without_summaries:
                title_text = attachment.get('text', 'Untitled Document')
                url = attachment.get('url', '')
                if url:
                    # Convert relative API URL to full URL
                    full_url = f"https://lacity.primegov.com{url}"
                    html += f"""                    <li><a href="{full_url}" class="doc-link" target="_blank">{title_text}</a></li>
"""
                else:
                    html += f"""                    <li>{title_text}</li>
"""

            html += """                </ul>
            </details>
        </section>
"""

    html += """    </main>
</body>
</html>
"""

    # Write file
    output_path = output_dir / f"{council_file}.html"
    output_path.write_text(html)
    print(f"Generated: {output_path}")


def generate_index_page(all_files: List[Dict[str, Any]], output_dir: Path) -> None:
    """Generate index page listing all council files."""

    # Sort by last_seen date (most recent first)
    sorted_files = sorted(
        all_files,
        key=lambda x: x.get('last_seen', ''),
        reverse=True
    )

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Council Files - LA Council Tracker</title>
    <meta name="description" content="Browse all LA City Council files with timelines and AI summaries">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background: #f5f5f5;
            padding-bottom: 2rem;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 1rem;
        }

        header {
            background: #fff;
            border-bottom: 1px solid #e0e0e0;
            padding: 1.5rem 0;
            margin-bottom: 1.5rem;
        }

        .breadcrumb {
            font-size: 0.875rem;
            color: #666;
            margin-bottom: 0.75rem;
        }

        .breadcrumb a {
            color: #0066cc;
            text-decoration: none;
        }

        .breadcrumb a:hover {
            text-decoration: underline;
        }

        h1 {
            font-size: 1.75rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #1a1a1a;
        }

        .subtitle {
            font-size: 1rem;
            color: #666;
        }

        .filters {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }

        .filter-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .filter-group label {
            font-size: 0.875rem;
            font-weight: 600;
            color: #666;
        }

        .filter-group input,
        .filter-group select {
            padding: 0.5rem;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            font-size: 0.875rem;
        }

        .stats {
            font-size: 0.875rem;
            color: #666;
            margin-bottom: 1.5rem;
        }

        .file-card {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: box-shadow 0.2s;
        }

        .file-card:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .file-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 0.75rem;
        }

        .file-number {
            font-size: 1rem;
            font-weight: 600;
            color: #0066cc;
        }

        .file-number a {
            color: inherit;
            text-decoration: none;
        }

        .file-number a:hover {
            text-decoration: underline;
        }

        .file-badges {
            display: flex;
            gap: 0.5rem;
        }

        .badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .badge-district {
            background: #f0f0f0;
            color: #666;
        }

        .badge-summary {
            background: #e8f4f8;
            color: #0066cc;
        }

        .file-title {
            font-size: 0.9375rem;
            color: #333;
            margin-bottom: 0.5rem;
            line-height: 1.5;
        }

        .file-meta {
            display: flex;
            gap: 1.5rem;
            font-size: 0.875rem;
            color: #666;
        }

        @media (max-width: 640px) {
            .filters {
                flex-direction: column;
                align-items: stretch;
            }

            .file-header {
                flex-direction: column;
                gap: 0.5rem;
            }

            .file-meta {
                flex-direction: column;
                gap: 0.25rem;
            }
        }
    </style>
    <script>
        function filterFiles() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const districtFilter = document.getElementById('district').value;
            const cards = document.querySelectorAll('.file-card');
            let visibleCount = 0;

            cards.forEach(card => {
                const title = card.dataset.title.toLowerCase();
                const number = card.dataset.number.toLowerCase();
                const district = card.dataset.district;

                const matchesSearch = title.includes(searchTerm) || number.includes(searchTerm);
                const matchesDistrict = !districtFilter || district === districtFilter;

                if (matchesSearch && matchesDistrict) {
                    card.style.display = '';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            document.getElementById('visible-count').textContent = visibleCount;
        }
    </script>
</head>
<body>
    <header>
        <div class="container">
            <div class="breadcrumb">
                <a href="../index.html">Home</a> / Council Files
            </div>
            <h1>Council Files</h1>
            <p class="subtitle">Track issues across multiple meetings</p>
        </div>
    </header>

    <main class="container">
        <div class="filters">
            <div class="filter-group">
                <label for="search">Search:</label>
                <input type="text" id="search" placeholder="File number or title..."
                       oninput="filterFiles()" style="min-width: 250px;">
            </div>
            <div class="filter-group">
                <label for="district">District:</label>
                <select id="district" onchange="filterFiles()">
                    <option value="">All Districts</option>
"""

    # Collect unique districts
    districts = set()
    for file_data in all_files:
        district = file_data.get('district', 'Unknown')
        if district and district != 'Unknown':
            districts.add(district)

    for district in sorted(districts):
        html += f'                    <option value="{district}">{district}</option>\n'

    html += f"""                </select>
            </div>
        </div>

        <div class="stats">
            Showing <span id="visible-count">{len(sorted_files)}</span> of {len(sorted_files)} council files
        </div>
"""

    # Generate file cards
    for file_data in sorted_files:
        council_file = file_data['council_file']
        title = file_data['title']
        district = file_data.get('district', 'Unknown')
        last_seen = format_date(file_data['last_seen'])
        stats = file_data.get('stats', {})
        appearances = stats.get('total_appearances', 0)
        has_summaries = stats.get('attachments_with_summaries', 0) > 0

        html += f"""        <div class="file-card"
             data-number="{council_file}"
             data-title="{title.replace('"', '&quot;')}"
             data-district="{district}">
            <div class="file-header">
                <div class="file-number">
                    <a href="{council_file}.html">{council_file}</a>
                </div>
"""

        # Only show badges if there's a valid district
        if district and district != 'Unknown':
            html += f"""                <div class="file-badges">
                    <span class="badge badge-district">{district}</span>
                </div>
"""

        html += f"""            </div>
            <div class="file-title">{title}</div>
            <div class="file-meta">
                <span>Last seen: {last_seen}</span>
                <span>{appearances} appearance(s)</span>
            </div>
        </div>
"""

    html += """    </main>
</body>
</html>
"""

    # Write index file
    index_path = output_dir / "index.html"
    index_path.write_text(html)
    print(f"Generated: {index_path}")


def main():
    """Generate all council file pages."""

    # Setup paths
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data' / 'councilfiles'
    output_dir = base_dir / 'site' / 'councilfiles'

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load all council files
    all_files = []
    for json_file in data_dir.glob('*.json'):
        if json_file.name == 'index.json':
            continue

        try:
            with open(json_file, 'r') as f:
                file_data = json.load(f)
                all_files.append(file_data)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    print(f"Loaded {len(all_files)} council files")

    # Load meeting metadata
    meetings_metadata = load_meeting_metadata()
    print(f"Loaded metadata for {len(meetings_metadata)} meetings")

    # Generate individual pages
    for file_data in all_files:
        try:
            generate_council_file_page(file_data, output_dir, meetings_metadata)
        except Exception as e:
            print(f"Error generating page for {file_data.get('council_file', 'unknown')}: {e}")

    # Generate index page
    generate_index_page(all_files, output_dir)

    print(f"\nComplete! Generated {len(all_files)} council file pages + index")
    print(f"Output directory: {output_dir}")


if __name__ == '__main__':
    main()
