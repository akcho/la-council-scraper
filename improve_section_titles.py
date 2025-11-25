#!/usr/bin/env python3
"""
Use AI to improve section titles in parsed agenda JSON files.

Transforms bureaucratic titles like "(Referred to the Government Operations...)"
into clearer, user-friendly titles like "Agenda Items".
"""

import json
import os
import re
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

AGENDAS_DIR = Path("data/agendas")

# Static mappings for common titles (no AI needed)
STATIC_IMPROVEMENTS = {
    "Items Noticed for Public Hearing": "Scheduled hearings",
    "Items for which Public Hearings Have Been Held": "Completed hearings",
    "Items for which Public Hearings Have Not Been Held - (10 Votes Required for Consideration)": "No hearings held (requires 10 votes)",
    "Closed Session": "Closed sessions",
    "Commendatory Resolutions, Introductions and Presentations": "Commendations and presentations",
    "Public Testimony of Non-agenda Items Within Jurisdiction of Council": "Public comments",
    "Multiple Agenda Item Comment": "General public comments",
    "MULTIPLE AGENDA ITEM COMMENT": "General public comments",
    "GENERAL PUBLIC COMMENT": "Public comments",
}


def is_title_unclear(title: str) -> bool:
    """Check if a title needs improvement."""
    if not title:
        return False

    # Already mapped
    if title in STATIC_IMPROVEMENTS:
        return False

    # Already improved (stored in agenda)
    if title.startswith("improved:"):
        return False

    # Looks like a referral note, not a real title
    if title.startswith("(Referred to"):
        return True

    # Very long titles are usually unclear
    if len(title) > 80:
        return True

    # Contains bureaucratic language
    bureaucratic_patterns = [
        r"^\(.*\)$",  # Entire title in parentheses
        r"Committee\s+Report",
        r"Fiscal Year \d{4}-\d{2}",
    ]

    for pattern in bureaucratic_patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return True

    return False


def improve_title_with_ai(title: str, items: list, client: Anthropic) -> str:
    """Use AI to create a better section title."""

    # Build context from items
    item_summaries = []
    for item in items[:5]:  # Use first 5 items for context
        item_title = item.get('title', item.get('raw_text', ''))[:200]
        if item_title:
            item_summaries.append(f"- {item_title}")

    items_context = "\n".join(item_summaries) if item_summaries else "No items in this section"

    prompt = f"""Given this section title from a city council meeting agenda:
"{title}"

And these items in the section:
{items_context}

Create a short, clear section title (2-5 words) that describes what these items are about.
Rules:
- Use sentence case (capitalize first word only)
- No punctuation at the end
- Be specific but concise
- If it's just general agenda items, use "Agenda items"

Return ONLY the new title, nothing else."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"  ⚠️ AI error: {e}")
        return "Agenda items"  # Fallback


def improve_agenda_titles(agenda_file: Path, client: Anthropic, dry_run: bool = False) -> int:
    """Improve section titles in an agenda file. Returns count of improvements."""

    with open(agenda_file, 'r', encoding='utf-8') as f:
        agenda = json.load(f)

    improved_count = 0
    sections = agenda.get('sections', [])

    for section in sections:
        original_title = section.get('title', '')

        # Check static mappings first
        if original_title in STATIC_IMPROVEMENTS:
            new_title = STATIC_IMPROVEMENTS[original_title]
            if original_title != new_title:
                section['original_title'] = original_title
                section['title'] = new_title
                improved_count += 1
                print(f"  📝 Static: '{original_title[:50]}...' → '{new_title}'")
            continue

        # Check if unclear and needs AI improvement
        if is_title_unclear(original_title):
            items = section.get('items', [])
            new_title = improve_title_with_ai(original_title, items, client)

            if new_title and new_title != original_title:
                section['original_title'] = original_title
                section['title'] = new_title
                improved_count += 1
                print(f"  🤖 AI: '{original_title[:50]}...' → '{new_title}'")

    # Save if changes were made
    if improved_count > 0 and not dry_run:
        with open(agenda_file, 'w', encoding='utf-8') as f:
            json.dump(agenda, f, indent=2, ensure_ascii=False)

    return improved_count


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Improve section titles in agenda files')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
    parser.add_argument('--meeting', type=int, help='Process specific meeting ID only')
    args = parser.parse_args()

    print("=" * 60)
    print("Section Title Improver")
    print("=" * 60)
    print()

    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set. Only static improvements will be applied.")
        client = None
    else:
        client = Anthropic(api_key=api_key)

    if not AGENDAS_DIR.exists():
        print(f"❌ Agendas directory not found: {AGENDAS_DIR}")
        return

    # Find agenda files
    if args.meeting:
        agenda_files = [AGENDAS_DIR / f"agenda_{args.meeting}.json"]
        if not agenda_files[0].exists():
            print(f"❌ Agenda file not found: {agenda_files[0]}")
            return
    else:
        agenda_files = sorted(AGENDAS_DIR.glob("agenda_*.json"))

    print(f"📋 Found {len(agenda_files)} agenda file(s)")
    if args.dry_run:
        print("🔍 DRY RUN - no changes will be saved\n")
    print()

    total_improved = 0

    for agenda_file in agenda_files:
        meeting_id = agenda_file.stem.replace('agenda_', '')
        print(f"📄 Processing meeting {meeting_id}...")

        improved = improve_agenda_titles(agenda_file, client, args.dry_run)
        total_improved += improved

        if improved == 0:
            print("  ✓ No improvements needed")

    print()
    print("=" * 60)
    print(f"✅ Improved {total_improved} section title(s)")
    if args.dry_run:
        print("   (dry run - no files were modified)")
    else:
        print("   Run 'python generate_site.py' to regenerate the site")
    print("=" * 60)


if __name__ == "__main__":
    main()
