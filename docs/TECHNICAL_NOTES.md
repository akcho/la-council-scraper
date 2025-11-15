# Technical Notes

Session-to-session reference for development. Updated incrementally as we discover new patterns and solve problems.

**📝 Update Instructions:**
- **Current Focus:** Replace the entire section each session with next 3-5 concrete actions (keep to 5-10 lines)
- **Data Access / Known Issues / Code Patterns:** Append new discoveries only, delete resolved issues
- This file should grow slowly - only add genuinely reusable information

---

## Current Focus (Updated: 2025-11-15)

**✅ Completed:**
- Fixed agenda access (PrimeGov API download URLs were broken/404)
- Found working solution: Portal page URLs with templateId
- Validated structure: Agendas are parseable HTML with `data-itemid` attributes

**🚧 Next Steps (Week 1 MVP):**
1. Define JSON schema for agenda items
2. Build agenda parser: HTML portal page → structured JSON
3. Test parser with 3 meetings: 17432, 17283, 17406
4. Update `fetch_meetings.py` to use portal URLs
5. Integrate parser into pipeline

**Goal:** Complete Week 1 from WEBSITE_PLANNING.md - have parseable agenda JSON for recent meetings.

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

---

## Reference Links

- PrimeGov API Base: `https://lacity.primegov.com`
- City Clerk Calendar: `https://clerk.lacity.gov/calendar`
- Planning Doc: `docs/gitignored/WEBSITE_PLANNING.md`
