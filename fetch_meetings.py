#!/usr/bin/env python3
"""
MVP: Fetch LA City Council meetings and prepare for summarization.
"""

import requests
import json
from datetime import datetime
from typing import List, Dict

class LACouncilScraper:
    """Fetch and process LA City Council meetings."""

    BASE_URL = "https://lacity.primegov.com"
    CITY_COUNCIL_ID = 1  # Committee ID for City Council

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_recent_meetings(self, limit: int = 10) -> List[Dict]:
        """Get recent City Council meetings (both upcoming and archived)."""

        all_meetings = []

        # Get upcoming meetings (includes today's meetings)
        print(f"📅 Fetching upcoming City Council meetings...")
        url = f"{self.BASE_URL}/api/v2/PublicPortal/ListUpcomingMeetings"

        response = self.session.get(url)
        response.raise_for_status()
        upcoming = response.json()

        upcoming_council = [
            m for m in upcoming
            if m.get('committeeId') == self.CITY_COUNCIL_ID
        ]
        all_meetings.extend(upcoming_council)
        print(f"✅ Found {len(upcoming_council)} upcoming City Council meetings")

        # Get archived meetings from current year
        current_year = datetime.now().year
        print(f"📅 Fetching archived City Council meetings for {current_year}...")
        url = f"{self.BASE_URL}/api/v2/PublicPortal/ListArchivedMeetings?year={current_year}"

        response = self.session.get(url)
        response.raise_for_status()

        archived = response.json()

        # Filter for City Council only
        archived_council = [
            m for m in archived
            if m.get('committeeId') == self.CITY_COUNCIL_ID
        ]
        all_meetings.extend(archived_council)
        print(f"✅ Found {len(archived_council)} archived City Council meetings")

        # Remove duplicates by ID and sort by date (most recent first)
        unique_meetings = {m['id']: m for m in all_meetings}.values()
        sorted_meetings = sorted(unique_meetings, key=lambda x: x.get('dateTime', ''), reverse=True)

        print(f"✅ Total: {len(sorted_meetings)} unique City Council meetings")

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
    print("LA City Council Scraper MVP")
    print("=" * 60)
    print()

    scraper = LACouncilScraper()

    # Get recent meetings
    meetings = scraper.get_recent_meetings(limit=5)

    if not meetings:
        print("❌ No meetings found!")
        return

    print(f"\n📋 Most Recent City Council Meetings:\n")

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
