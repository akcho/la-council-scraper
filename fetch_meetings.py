#!/usr/bin/env python3
"""
Fetch LA City Council and committee meetings and prepare for summarization.
"""

import requests
import json
from datetime import datetime
from typing import List, Dict

class LACouncilScraper:
    """Fetch and process LA City Council and committee meetings."""

    BASE_URL = "https://lacity.primegov.com"

    # Committee name mapping (from PrimeGov API - verified against actual API data)
    COMMITTEE_NAMES = {
        1: "City Council Meeting",
        4: "Public Safety Committee",
        6: "Los Angeles City Health Commission",
        12: "Planning and Land Use Management Committee",
        15: "Rules, Elections and Intergovernmental Relations Committee",
        17: "Transportation Committee",
        18: "Trade, Travel and Tourism Committee",
        19: "Budget and Finance Committee",
        32: "Economic Development and Jobs Committee",
        36: "Public Works Committee",
        49: "Energy and Environment Committee",
        101: "Civil Rights, Equity, Immigration, Aging, and Disability Committee",
        103: "Government Operations Committee",
        104: "Housing and Homelessness Committee",
        108: "Arts, Parks, Libraries, and Community Enrichment Committee",
        109: "Government Efficiency, Innovation, and Audits Committee",
        110: "Personnel and Hiring Committee",
        112: "Ad Hoc Committee for LA Recovery",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_committee_name(self, committee_id: int, fallback_title: str = None) -> str:
        """Get committee name from ID, with fallback to provided title."""
        if committee_id in self.COMMITTEE_NAMES:
            return self.COMMITTEE_NAMES[committee_id]
        if fallback_title:
            return fallback_title
        return f"Committee {committee_id}"

    def get_recent_meetings(self, limit: int = 50, committee_id: int = None) -> List[Dict]:
        """Get recent meetings (both upcoming and archived).

        Args:
            limit: Maximum number of meetings to return
            committee_id: If provided, filter to this committee only. None = all committees.
        """

        all_meetings = []

        # Get upcoming meetings (includes today's meetings)
        # Note: upcoming meetings API includes committee 'title' field
        if committee_id:
            print(f"📅 Fetching upcoming {self.get_committee_name(committee_id)} meetings...")
        else:
            print(f"📅 Fetching upcoming meetings (all committees)...")
        url = f"{self.BASE_URL}/api/v2/PublicPortal/ListUpcomingMeetings"

        response = self.session.get(url)
        response.raise_for_status()
        upcoming = response.json()

        # Add committee name to each meeting from upcoming (has 'title' field)
        for m in upcoming:
            cid = m.get('committeeId')
            # Use 'title' from API response as fallback (it has committee name)
            m['committeeName'] = self.get_committee_name(cid, m.get('title'))

        if committee_id:
            upcoming = [m for m in upcoming if m.get('committeeId') == committee_id]

        all_meetings.extend(upcoming)
        print(f"✅ Found {len(upcoming)} upcoming meetings")

        # Get archived meetings from current year
        current_year = datetime.now().year
        if committee_id:
            print(f"📅 Fetching archived {self.get_committee_name(committee_id)} meetings for {current_year}...")
        else:
            print(f"📅 Fetching archived meetings for {current_year} (all committees)...")
        url = f"{self.BASE_URL}/api/v2/PublicPortal/ListArchivedMeetings?year={current_year}"

        response = self.session.get(url)
        response.raise_for_status()

        archived = response.json()

        # Add committee name to each archived meeting
        for m in archived:
            cid = m.get('committeeId')
            m['committeeName'] = self.get_committee_name(cid)

        if committee_id:
            archived = [m for m in archived if m.get('committeeId') == committee_id]

        all_meetings.extend(archived)
        print(f"✅ Found {len(archived)} archived meetings")

        # Remove duplicates by ID and sort by date (most recent first)
        unique_meetings = {m['id']: m for m in all_meetings}.values()
        sorted_meetings = sorted(unique_meetings, key=lambda x: x.get('dateTime', ''), reverse=True)

        print(f"✅ Total: {len(sorted_meetings)} unique meetings")

        return list(sorted_meetings)[:limit]

    def get_meeting_details(self, meeting_id: int) -> Dict:
        """Get detailed information about a specific meeting."""

        print(f"🔍 Fetching details for meeting {meeting_id}...")

        # Try different endpoint patterns
        endpoints = [
            f"{self.BASE_URL}/Portal/Meeting?meetingTemplateId={meeting_id}",
            f"{self.BASE_URL}/api/meeting/{meeting_id}",
        ]

        for endpoint in endpoints:
            try:
                response = self.session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    return response.json() if 'json' in response.headers.get('content-type', '') else {}
            except:
                continue

        print(f"⚠️  Couldn't fetch details for meeting {meeting_id}")
        return {}

    def get_agenda_portal_url(self, meeting: Dict) -> str:
        """
        Get the portal URL for the HTML agenda.

        Uses templateId (not document id) to construct working portal URLs.
        This is the correct way to access agendas - DownloadFile URLs return 404.
        """
        doc_list = meeting.get('documentList', [])

        # Find HTML Agenda document
        html_agenda = next((d for d in doc_list if d.get('templateName') == 'HTML Agenda'), None)

        if html_agenda:
            template_id = html_agenda.get('templateId')
            if template_id:
                return f"{self.BASE_URL}/Portal/Meeting?meetingTemplateId={template_id}"

        return None

    def get_document_url(self, meeting: Dict, doc_type: str = "HTML Agenda") -> str:
        """
        DEPRECATED: DownloadFile URLs return 404.
        Use get_agenda_portal_url() instead.

        Extract document URL from meeting data.
        """
        doc_list = meeting.get('documentList', [])

        # Try to find HTML agenda first (easier to parse than PDF)
        for doc in doc_list:
            template_name = doc.get('templateName', '')
            if doc_type in template_name:
                doc_id = doc.get('id')
                if doc_id:
                    return f"{self.BASE_URL}/Portal/DownloadFile/{doc_id}"

        # Fallback to any agenda
        for doc in doc_list:
            if 'Agenda' in doc.get('templateName', ''):
                doc_id = doc.get('id')
                if doc_id:
                    return f"{self.BASE_URL}/Portal/DownloadFile/{doc_id}"

        return None

    def fetch_document_content(self, url: str) -> str:
        """Fetch and return document content."""

        if not url:
            return None

        print(f"📄 Downloading document from {url}...")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '')

            if 'html' in content_type:
                return response.text
            elif 'pdf' in content_type:
                # For now, just note that it's a PDF
                # We'll need to add PDF parsing later
                return f"[PDF Document - {len(response.content)} bytes]"
            else:
                return response.text

        except Exception as e:
            print(f"❌ Error downloading document: {e}")
            return None

    def get_youtube_url(self, meeting: Dict) -> str:
        """Extract YouTube URL if available."""
        return meeting.get('videoUrl')

    def format_meeting_summary(self, meeting: Dict) -> str:
        """Format basic meeting info as markdown."""

        title = meeting.get('title', 'Unknown Meeting')
        date = meeting.get('date', 'Unknown Date')
        time = meeting.get('time', 'Unknown Time')
        meeting_id = meeting.get('id')
        video_url = self.get_youtube_url(meeting)
        portal_url = self.get_agenda_portal_url(meeting)

        summary = f"""# {title}
**Date:** {date}
**Time:** {time}
**Meeting ID:** {meeting_id}

"""

        if video_url:
            summary += f"**Video:** {video_url}\n\n"

        if portal_url:
            summary += f"**Agenda:** {portal_url}\n\n"

        # List available documents
        doc_list = meeting.get('documentList', [])
        if doc_list:
            summary += "**Available Documents:**\n"
            for doc in doc_list:
                template_name = doc.get('templateName', 'Unknown')
                summary += f"- {template_name}\n"

        return summary


def main():
    """Main function to test the scraper."""

    print("=" * 60)
    print("LA City Council & Committee Meeting Scraper")
    print("=" * 60)
    print()

    scraper = LACouncilScraper()

    # Get recent meetings from ALL committees
    meetings = scraper.get_recent_meetings(limit=50)

    if not meetings:
        print("❌ No meetings found!")
        return

    print(f"\n📋 Most Recent Meetings (all committees):\n")

    for i, meeting in enumerate(meetings, 1):
        print(f"\n{'-' * 60}")
        print(scraper.format_meeting_summary(meeting))

        # Try to get agenda content for first meeting
        if i == 1:
            print("\n🔍 Trying to fetch agenda content...\n")
            portal_url = scraper.get_agenda_portal_url(meeting)
            if portal_url:
                content = scraper.fetch_document_content(portal_url)
                if content:
                    # Save to file
                    filename = f"meeting_{meeting['id']}_agenda.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Saved agenda to {filename}")
                    print(f"   Content length: {len(content)} characters")

    # Save meetings data
    print("\n" + "=" * 60)
    print("💾 Saving meetings data...")
    with open('recent_meetings.json', 'w') as f:
        json.dump(meetings, f, indent=2)
    print("✅ Saved to recent_meetings.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
