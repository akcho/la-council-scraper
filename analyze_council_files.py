#!/usr/bin/env python3
"""
Analyze council files across all agenda JSONs to understand patterns:
- Count unique council files
- Find files appearing in multiple meetings
- Identify rich examples with multiple attachments
"""

import json
from pathlib import Path
from collections import defaultdict
import sys

def load_agendas():
    """Load all agenda JSON files."""
    agenda_dir = Path("data/agendas")
    agendas = []

    for json_file in sorted(agenda_dir.glob("agenda_*.json")):
        with open(json_file) as f:
            data = json.load(f)
            agendas.append({
                'file': json_file.name,
                'meeting_id': json_file.stem.replace('agenda_', ''),
                'data': data
            })

    return agendas

def analyze_council_files(agendas):
    """Analyze council file patterns across all meetings."""

    # Track council files
    council_files = defaultdict(lambda: {
        'meetings': [],
        'total_items': 0,
        'total_attachments': 0,
        'example_items': []
    })

    total_items = 0
    items_with_council_file = 0

    for agenda in agendas:
        meeting_id = agenda['meeting_id']
        data = agenda['data']

        # Parse agenda items from sections
        for section in data.get('sections', []):
            for item in section.get('items', []):
                total_items += 1

                council_file = item.get('council_file', '').strip()
                if council_file:
                    items_with_council_file += 1

                    # Track this council file
                    cf_data = council_files[council_file]
                    cf_data['meetings'].append(meeting_id)
                    cf_data['total_items'] += 1

                    # Count attachments
                    num_attachments = len(item.get('attachments', []))
                    cf_data['total_attachments'] += num_attachments

                    # Store example items (limit to 3 per council file)
                    if len(cf_data['example_items']) < 3:
                        # Extract historyId from attachment URLs for better tracking
                        processed_attachments = []
                        for att in item.get('attachments', []):
                            url = att.get('url', '')
                            history_id = None
                            if 'historyId=' in url:
                                history_id = url.split('historyId=')[-1]

                            processed_attachments.append({
                                'text': att.get('text', 'Unnamed'),
                                'url': url,
                                'historyId': history_id
                            })

                        cf_data['example_items'].append({
                            'meeting_id': meeting_id,
                            'title': item.get('title', '')[:100],
                            'num_attachments': num_attachments,
                            'attachments': processed_attachments
                        })

    return council_files, total_items, items_with_council_file

def print_analysis(council_files, total_items, items_with_council_file):
    """Print analysis results."""

    print("=" * 80)
    print("COUNCIL FILE ANALYSIS")
    print("=" * 80)
    print()

    print(f"Total agenda items across all meetings: {total_items}")
    print(f"Items with council file numbers: {items_with_council_file} ({items_with_council_file/total_items*100:.1f}%)")
    print(f"Unique council files: {len(council_files)}")
    print()

    # Find files appearing in multiple meetings
    multi_meeting = {cf: data for cf, data in council_files.items()
                     if len(set(data['meetings'])) > 1}

    print(f"Council files appearing in multiple meetings: {len(multi_meeting)}")
    print()

    # Find richest examples (most attachments)
    richest = sorted(council_files.items(),
                     key=lambda x: x[1]['total_attachments'],
                     reverse=True)[:10]

    print("=" * 80)
    print("TOP 10 COUNCIL FILES BY ATTACHMENT COUNT")
    print("=" * 80)
    print()

    for cf, data in richest:
        meetings = set(data['meetings'])
        print(f"Council File: {cf}")
        print(f"  Appearances: {len(meetings)} meeting(s) - {sorted(meetings)}")
        print(f"  Total items: {data['total_items']}")
        print(f"  Total attachments: {data['total_attachments']}")

        if data['example_items']:
            print(f"  Example: {data['example_items'][0]['title']}")
        print()

    # Show multi-meeting examples
    if multi_meeting:
        print("=" * 80)
        print("COUNCIL FILES APPEARING IN MULTIPLE MEETINGS (showing top 5)")
        print("=" * 80)
        print()

        sorted_multi = sorted(multi_meeting.items(),
                             key=lambda x: (len(set(x[1]['meetings'])), x[1]['total_attachments']),
                             reverse=True)[:5]

        for cf, data in sorted_multi:
            meetings = sorted(set(data['meetings']))
            print(f"Council File: {cf}")
            print(f"  Meetings: {meetings} ({len(meetings)} total)")
            print(f"  Total attachments: {data['total_attachments']}")

            for idx, item in enumerate(data['example_items'], 1):
                print(f"  Item {idx} (meeting {item['meeting_id']}): {item['title']}")
                print(f"    Attachments: {item['num_attachments']}")
            print()

    # Find best prototype example
    print("=" * 80)
    print("BEST PROTOTYPE CANDIDATES")
    print("=" * 80)
    print()
    print("Looking for council files with:")
    print("  - Multiple attachments (for testing PDF processing)")
    print("  - Preferably appears in multiple meetings (shows progression)")
    print()

    # Score candidates: attachments * (1 + 0.5 * multi_meeting_bonus)
    candidates = []
    for cf, data in council_files.items():
        num_meetings = len(set(data['meetings']))
        score = data['total_attachments'] * (1 + 0.5 * (num_meetings - 1))
        candidates.append((score, cf, data))

    candidates.sort(reverse=True)

    for idx, (score, cf, data) in enumerate(candidates[:5], 1):
        meetings = sorted(set(data['meetings']))
        print(f"{idx}. Council File: {cf}")
        print(f"   Score: {score:.1f} | Meetings: {len(meetings)} | Attachments: {data['total_attachments']}")

        for item in data['example_items'][:2]:
            print(f"   - {item['title']}")
            print(f"     Meeting {item['meeting_id']}, {item['num_attachments']} attachments")

            # Show actual attachment details for top candidate
            if idx == 1 and item['attachments']:
                print(f"     Attachment details:")
                for att in item['attachments'][:3]:
                    # Filter out "Attachment" preview links, only show actual docs
                    if att.get('historyId'):
                        print(f"       • {att.get('text', 'Unnamed')}")
                        print(f"         ID: {att.get('historyId')}")
        print()

def main():
    print("Loading agenda data...")
    agendas = load_agendas()
    print(f"Loaded {len(agendas)} agenda files")
    print()

    print("Analyzing council files...")
    council_files, total_items, items_with_council_file = analyze_council_files(agendas)

    print_analysis(council_files, total_items, items_with_council_file)

    # Export detailed data for further analysis
    output_file = Path("data/council_file_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert defaultdict to regular dict for JSON serialization
    export_data = {
        cf: {
            'meetings': sorted(set(data['meetings'])),
            'total_items': data['total_items'],
            'total_attachments': data['total_attachments'],
            'example_items': data['example_items']
        }
        for cf, data in council_files.items()
    }

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"Detailed analysis exported to: {output_file}")

if __name__ == "__main__":
    main()
