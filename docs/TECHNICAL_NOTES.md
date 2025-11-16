# Technical Notes

Session-to-session reference for development. Updated incrementally as we discover new patterns and solve problems.

**📝 Update Instructions:**
- **Current Focus:** Replace the entire section each session with next 3-5 concrete actions (keep to 5-10 lines)
- **Data Access / Known Issues / Code Patterns:** Append new discoveries only, delete resolved issues
- This file should grow slowly - only add genuinely reusable information

---

## Current Focus (Updated: 2025-11-15)

**✅ Week 1 MVP - COMPLETED:**
1. ✅ Defined JSON schema for agenda items ([agenda_schema.json](../agenda_schema.json))
2. ✅ Built agenda parser: HTML → structured JSON ([parse_agenda.py](../parse_agenda.py))
3. ✅ Tested parser with 7 meetings (17432, 17283, 17406, 17407, 17367, 17455, 17477)
4. ✅ Updated `fetch_meetings.py` with `get_agenda_portal_url()` method
5. ✅ Integrated parser into pipeline ([parse_agendas.py](../parse_agendas.py))
6. ✅ Updated `run_pipeline.py` to include agenda parsing step
7. ✅ Stored 7 parsed agendas in `data/agendas/` (550KB total, JSON format)

**🚧 Next Steps (Week 2 MVP):**
1. Create mobile-first HTML template for meeting pages
2. Build static page generator (JSON → HTML)
3. Add analytics (Plausible/Umami)
4. Deploy to hosting (GitHub Pages/Netlify/Vercel)
5. Add link to next Reddit comment

**Goal:** Deploy first meeting page and validate CTR from Reddit.

---

## Data Access

### Agenda Access (Solved: 2025-11-15)

**Problem:** PrimeGov API provides broken download URLs
- API endpoint: `https://lacity.primegov.com/Portal/DownloadFile/{doc_id}`
- Result: 404 error page ❌

**Solution:** Use portal page URLs
```python
# Get meeting from API
meeting = api_response['meetings'][0]
docs = meeting.get('documentList', [])

# Find HTML Agenda document
html_agenda = next((d for d in docs if d.get('templateName') == 'HTML Agenda'), None)
template_id = html_agenda.get('templateId')  # NOT the doc 'id'!

# Construct portal URL
portal_url = f"https://lacity.primegov.com/Portal/Meeting?meetingTemplateId={template_id}"
```

**Example:**
- Meeting ID: 17432 (Nov 14, 2025)
- Template ID: 147181
- URL: `https://lacity.primegov.com/Portal/Meeting?meetingTemplateId=147181`
- Result: 666KB HTML page with 13 sections, 6 agenda items ✅

### Agenda HTML Structure

**Sections:**
```html
<div data-sectionid="357193">
  <!-- Section headers like "Roll Call", "Approval of Minutes" -->
</div>
```

**Agenda Items:**
```html
<div class="meeting-item" data-itemid="155866" data-hasattachments="True">
  <table class="item-table">
    <tr>
      <td class="number-cell">(1)</td>
      <td class="item-cell">
        <!-- Council file number, title, full recommendation text -->
      </td>
    </tr>
  </table>
</div>
```

**Parsing with BeautifulSoup:**
```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, 'html.parser')

# Get all agenda items
items = soup.find_all(attrs={'data-itemid': True})

for item in items:
    item_id = item.get('data-itemid')
    item_number = item.find(class_='number-cell').get_text(strip=True)
    item_content = item.find(class_='item-cell').get_text(strip=True)
    # Parse content for: council file number, title, recommendation, etc.
```

**Sample Item:**
```
Item Number: (1)
Item ID: 155866
Council File: 25-0160-S93CD 10
Title: CONTINUED CONSIDERATION OF HEARING PROTEST, APPEALS OR OBJECTIONS...
```

### Meeting API Access

**Get archived meetings:**
```python
url = "https://lacity.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=2025"
response = requests.get(url)
meetings = response.json()

# Filter for City Council (committeeId = 1)
council_meetings = [m for m in meetings if m.get('committeeId') == 1]
```

**Get upcoming meetings:**
```python
url = "https://lacity.primegov.com/api/v2/PublicPortal/ListUpcomingMeetings"
response = requests.get(url)
meetings = response.json()
```

---

## Known Issues

### Current
- None (agenda access solved)

### Resolved
- ✅ PrimeGov download URLs return 404 → Use portal URLs instead

---

## Code Patterns

### BeautifulSoup HTML Parsing
```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, 'html.parser')

# Find elements by data attribute
items = soup.find_all(attrs={'data-itemid': True})

# Find by class
number_cell = item.find(class_='number-cell')

# Get text content
text = element.get_text(strip=True)
```

### Testing Portal URLs
```python
# Test pattern (see fetch_meetings.py for full implementation)
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

url = f"https://lacity.primegov.com/Portal/Meeting?meetingTemplateId={template_id}"
response = session.get(url, timeout=30)

if response.status_code == 200:
    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all(attrs={'data-itemid': True})
```

### Agenda Parsing Workflow (2025-11-15)

**Full pipeline now includes agenda parsing:**
```bash
python run_pipeline.py
# Step 1: Fetch meetings → recent_meetings.json
# Step 2: Parse agendas → data/agendas/agenda_{meeting_id}.json
# Step 3: Get transcripts
# Step 4: Generate summaries
```

**Standalone agenda parsing:**
```bash
python parse_agendas.py
# Reads: recent_meetings.json
# Outputs: data/agendas/agenda_{meeting_id}.json
# Skips: Already-parsed meetings
```

**Parse single agenda:**
```bash
python parse_agenda.py <html_file> <meeting_id> <template_id> [output_file]
# Example:
python parse_agenda.py meeting.html 17432 147181 agenda.json
```

**JSON Schema:**
- Schema: `agenda_schema.json`
- Structure: meeting → sections → items
- Each item: council_file, district, title, recommendation, attachments
- Stored permanently in `data/agendas/` (not deleted by cleanup)

---

## Reference Links

- PrimeGov API Base: `https://lacity.primegov.com`
- City Clerk Calendar: `https://clerk.lacity.gov/calendar`
- Planning Doc: `docs/gitignored/WEBSITE_PLANNING.md`
