#!/usr/bin/env python3
"""
Parse LA City Council agenda HTML into structured JSON.

Converts portal page HTML (from meetingTemplateId URLs) into a structured
JSON format following agenda_schema.json.
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup, Tag


class AgendaParser:
    """Parse LA City Council agenda HTML into structured JSON."""

    def __init__(self, html_content: str, meeting_id: int, template_id: int):
        """
        Initialize parser with HTML content.

        Args:
            html_content: Raw HTML from portal page
            meeting_id: PrimeGov meeting ID
            template_id: Template ID used to fetch the HTML
        """
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.meeting_id = meeting_id
        self.template_id = template_id
        self.portal_url = f"https://lacity.primegov.com/Portal/Meeting?meetingTemplateId={template_id}"

    def parse(self) -> Dict:
        """
        Parse the HTML and return structured JSON.

        Returns:
            Dictionary following agenda_schema.json format
        """
        sections = self._parse_sections()
        total_items = sum(len(section['items']) for section in sections)

        return {
            'meeting_id': self.meeting_id,
            'template_id': self.template_id,
            'parsed_at': datetime.now().isoformat(),
            'portal_url': self.portal_url,
            'sections': sections,
            'total_items': total_items,
            'total_sections': len(sections)
        }

    def _parse_sections(self) -> List[Dict]:
        """Parse all sections from the HTML."""
        sections = []
        section_elements = self.soup.find_all(attrs={'data-sectionid': True})

        for section_el in section_elements:
            section_id = section_el.get('data-sectionid')

            # Find section title
            title = self._extract_section_title(section_el)

            # Parse items within this section
            items = self._parse_items_in_section(section_el)

            sections.append({
                'section_id': section_id,
                'title': title,
                'items': items
            })

        return sections

    def _extract_section_title(self, section_el: Tag) -> str:
        """Extract the title/header from a section element."""
        # Try common header elements
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b']:
            header = section_el.find(tag)
            if header:
                return header.get_text(strip=True)

        # Fallback: look for any prominent text
        text = section_el.get_text(strip=True)
        if text:
            # Return first line if multiline
            first_line = text.split('\n')[0].strip()
            if first_line and len(first_line) < 200:
                return first_line

        return "Untitled Section"

    def _parse_items_in_section(self, section_el: Tag) -> List[Dict]:
        """Parse all agenda items within a section."""
        items = []
        item_elements = section_el.find_all(attrs={'data-itemid': True})

        for item_el in item_elements:
            item = self._parse_single_item(item_el)
            if item:
                items.append(item)

        return items

    def _parse_single_item(self, item_el: Tag) -> Optional[Dict]:
        """Parse a single agenda item element."""
        # Extract attributes
        item_id = item_el.get('data-itemid')
        has_attachments = item_el.get('data-hasattachments', 'False') == 'True'
        video_location = item_el.get('data-videolocation')
        mig = item_el.get('data-mig')

        # Extract item number
        number_cell = item_el.find(class_='number-cell')
        item_number = number_cell.get_text(strip=True) if number_cell else ''

        # Extract item content
        item_cell = item_el.find(class_='item-cell')
        if not item_cell:
            return None

        # Get raw text
        raw_text = item_cell.get_text(separator='\n', strip=True)

        # Parse structured fields from text
        council_file = self._extract_council_file(raw_text)
        district = self._extract_district(raw_text)
        title = self._extract_title(raw_text)
        recommendation = self._extract_recommendation(raw_text)

        # Extract attachments/links
        attachments = self._extract_attachments(item_cell)

        item = {
            'item_id': item_id,
            'item_number': item_number,
            'has_attachments': has_attachments,
            'raw_text': raw_text
        }

        # Add optional fields only if they exist
        if council_file:
            item['council_file'] = council_file
        if district:
            item['district'] = district
        if title:
            item['title'] = title
        if recommendation:
            item['recommendation'] = recommendation
        if video_location:
            item['video_location'] = video_location
        if mig:
            item['mig'] = mig
        if attachments:
            item['attachments'] = attachments

        return item

    def _extract_council_file(self, text: str) -> Optional[str]:
        """Extract council file number like '25-0160-S93'."""
        # Pattern: YY-NNNN or YY-NNNN-XXX
        match = re.search(r'\b(\d{2}-\d{4}(?:-[A-Z0-9]+)?)\b', text)
        return match.group(1) if match else None

    def _extract_district(self, text: str) -> Optional[str]:
        """Extract council district like 'CD 10'."""
        match = re.search(r'\b(CD \d+)\b', text)
        return match.group(1) if match else None

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract the main title/subject of the item."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        if not lines:
            return None

        # The title is usually the first substantial line after council file/district
        # Skip lines that are just council file numbers or districts
        for line in lines:
            # Skip if it's just a council file number (with optional suffix)
            if re.match(r'^(\d{2}-\d{4}(?:-[A-Z0-9]+)?)$', line):
                continue
            # Skip if it's just a district
            if re.match(r'^CD \d+$', line):
                continue
            # Skip if it's "Recommendation for Council action"
            if 'Recommendation for Council action' in line:
                continue
            # This should be the title - make sure it's substantial
            if len(line) > 15:  # Reasonable title length
                return line

        # Fallback: return first non-trivial line
        return lines[0] if lines else None

    def _extract_recommendation(self, text: str) -> Optional[str]:
        """Extract the recommendation text."""
        # Look for "Recommendation for Council action:" or similar
        match = re.search(r'Recommendation[^:]*:(.*?)(?=\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
        if match:
            rec = match.group(1).strip()
            # Clean up excessive whitespace
            rec = re.sub(r'\s+', ' ', rec)
            return rec if rec else None
        return None

    def _extract_attachments(self, item_cell: Tag) -> List[Dict]:
        """Extract attachment links from item cell."""
        attachments = []
        links = item_cell.find_all('a', href=True)

        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Skip empty or very short links
            if not href or len(href) < 5:
                continue

            attachments.append({
                'text': text if text else 'Attachment',
                'url': href
            })

        return attachments


def parse_agenda_file(html_file: str, meeting_id: int, template_id: int, output_file: str = None) -> Dict:
    """
    Parse an agenda HTML file and optionally save to JSON.

    Args:
        html_file: Path to HTML file
        meeting_id: PrimeGov meeting ID
        template_id: Template ID
        output_file: Optional path to save JSON output

    Returns:
        Parsed agenda dictionary
    """
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    parser = AgendaParser(html_content, meeting_id, template_id)
    agenda = parser.parse()

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(agenda, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved parsed agenda to {output_file}")

    return agenda


def main():
    """Test the parser with the sample agenda."""
    import sys

    if len(sys.argv) < 4:
        print("Usage: python parse_agenda.py <html_file> <meeting_id> <template_id> [output_file]")
        print("\nExample:")
        print("  python parse_agenda.py /tmp/sample_agenda.html 17432 147181 agenda_17432.json")
        sys.exit(1)

    html_file = sys.argv[1]
    meeting_id = int(sys.argv[2])
    template_id = int(sys.argv[3])
    output_file = sys.argv[4] if len(sys.argv) > 4 else None

    agenda = parse_agenda_file(html_file, meeting_id, template_id, output_file)

    # Print summary
    print(f"\n📋 Parsed Agenda Summary:")
    print(f"   Meeting ID: {agenda['meeting_id']}")
    print(f"   Template ID: {agenda['template_id']}")
    print(f"   Total Sections: {agenda['total_sections']}")
    print(f"   Total Items: {agenda['total_items']}")
    print(f"   Portal URL: {agenda['portal_url']}")

    # Show first few items
    print(f"\n📝 First 3 items:")
    item_count = 0
    for section in agenda['sections']:
        for item in section['items']:
            if item_count >= 3:
                break
            print(f"\n   Item {item['item_number']}:")
            print(f"     ID: {item['item_id']}")
            if 'council_file' in item:
                print(f"     Council File: {item['council_file']}")
            if 'district' in item:
                print(f"     District: {item['district']}")
            if 'title' in item:
                title = item['title'][:80] + '...' if len(item['title']) > 80 else item['title']
                print(f"     Title: {title}")
            item_count += 1
        if item_count >= 3:
            break


if __name__ == "__main__":
    main()
