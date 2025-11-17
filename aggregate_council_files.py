#!/usr/bin/env python3
"""
Council File Aggregation Script

Combines data for each council file across multiple meetings into a single JSON.
Creates data/councilfiles/{council_file_number}.json with:
- File metadata (number, title, district, status)
- Timeline of appearances across meetings
- All attachments with PDF summaries where available
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Directories
AGENDAS_DIR = Path("data/agendas")
PDF_SUMMARIES_DIR = Path("data/pdf_summaries")
COUNCILFILES_DIR = Path("data/councilfiles")

# Ensure output directory exists
COUNCILFILES_DIR.mkdir(parents=True, exist_ok=True)


def load_pdf_summaries():
    """Load all PDF summaries into a dictionary keyed by historyId."""
    summaries = {}

    if not PDF_SUMMARIES_DIR.exists():
        print(f"⚠️  No PDF summaries directory found at {PDF_SUMMARIES_DIR}")
        return summaries

    for summary_file in PDF_SUMMARIES_DIR.glob("*.json"):
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            summaries[data["historyId"]] = data

    print(f"📊 Loaded {len(summaries)} PDF summaries")
    return summaries


def extract_history_id_from_url(url):
    """Extract historyId from attachment URL."""
    if "historyId=" in url:
        return url.split("historyId=")[-1]
    return None


def aggregate_council_files():
    """Aggregate all council files across all meetings."""

    print("=" * 70)
    print("Council File Aggregation")
    print("=" * 70)

    # Load PDF summaries
    pdf_summaries = load_pdf_summaries()

    # Dictionary to collect data by council file
    council_files = defaultdict(lambda: {
        "council_file": None,
        "title": None,
        "district": None,
        "appearances": [],
        "attachments": [],
        "first_seen": None,
        "last_seen": None
    })

    # Process each agenda file
    agenda_files = sorted(AGENDAS_DIR.glob("agenda_*.json"))
    print(f"\n📂 Processing {len(agenda_files)} agenda files...")

    for agenda_file in agenda_files:
        with open(agenda_file, 'r', encoding='utf-8') as f:
            agenda = json.load(f)

        meeting_id = agenda["meeting_id"]
        parsed_at = agenda["parsed_at"]

        # Process each section
        for section in agenda["sections"]:
            for item in section["items"]:
                council_file = item.get("council_file")

                if not council_file:
                    continue

                # Initialize or update council file data
                cf = council_files[council_file]

                if cf["council_file"] is None:
                    cf["council_file"] = council_file
                    cf["title"] = item.get("title", "")
                    cf["district"] = item.get("district", "")

                # Track first/last seen
                if cf["first_seen"] is None or parsed_at < cf["first_seen"]:
                    cf["first_seen"] = parsed_at
                if cf["last_seen"] is None or parsed_at > cf["last_seen"]:
                    cf["last_seen"] = parsed_at

                # Add appearance
                appearance = {
                    "meeting_id": meeting_id,
                    "date": parsed_at,
                    "section": section["title"],
                    "item_number": item.get("item_number", ""),
                    "recommendation": item.get("recommendation", "")
                }
                cf["appearances"].append(appearance)

                # Process attachments
                for attachment in item.get("attachments", []):
                    history_id = extract_history_id_from_url(attachment.get("url", ""))

                    if not history_id:
                        continue

                    attachment_data = {
                        "historyId": history_id,
                        "text": attachment.get("text", ""),
                        "url": attachment.get("url", ""),
                        "meeting_id": meeting_id,
                        "has_summary": history_id in pdf_summaries
                    }

                    # Add PDF summary if available
                    if history_id in pdf_summaries:
                        summary_data = pdf_summaries[history_id]
                        attachment_data["summary"] = summary_data["summary"]
                        attachment_data["processing"] = summary_data["processing"]

                    cf["attachments"].append(attachment_data)

    print(f"✅ Found {len(council_files)} unique council files")

    # Save each council file
    print(f"\n💾 Saving council file data...")

    saved = 0
    for council_file, data in council_files.items():
        # Sort appearances by date
        data["appearances"].sort(key=lambda x: x["date"])

        # Add summary stats
        data["stats"] = {
            "total_appearances": len(data["appearances"]),
            "total_attachments": len(data["attachments"]),
            "attachments_with_summaries": sum(1 for a in data["attachments"] if a["has_summary"])
        }

        # Save to file
        output_file = COUNCILFILES_DIR / f"{council_file}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        saved += 1

    print(f"✅ Saved {saved} council file JSONs to {COUNCILFILES_DIR}")

    # Generate index file
    index = []
    for council_file, data in council_files.items():
        index.append({
            "council_file": council_file,
            "title": data["title"],
            "district": data["district"],
            "appearances": data["stats"]["total_appearances"],
            "attachments": data["stats"]["total_attachments"],
            "first_seen": data["first_seen"],
            "last_seen": data["last_seen"]
        })

    # Sort by last_seen (most recent first)
    index.sort(key=lambda x: x["last_seen"], reverse=True)

    index_file = COUNCILFILES_DIR / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_files": len(index),
            "files": index
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated index at {index_file}")

    print("\n" + "=" * 70)
    print("✅ AGGREGATION COMPLETE")
    print("=" * 70)

    # Show some stats
    total_with_summaries = sum(1 for cf in council_files.values()
                               if cf["stats"]["attachments_with_summaries"] > 0)

    print(f"\n📊 Summary Statistics:")
    print(f"   Total council files: {len(council_files)}")
    print(f"   Files with PDF summaries: {total_with_summaries}")
    print(f"   Total appearances: {sum(cf['stats']['total_appearances'] for cf in council_files.values())}")
    print(f"   Total attachments: {sum(cf['stats']['total_attachments'] for cf in council_files.values())}")
    print(f"   Attachments with summaries: {sum(cf['stats']['attachments_with_summaries'] for cf in council_files.values())}")

    return 0


if __name__ == "__main__":
    exit(aggregate_council_files())
