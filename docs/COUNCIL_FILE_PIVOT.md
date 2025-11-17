# Council File Pivot - Planning Doc

**Date:** 2025-11-16
**Status:** Planning phase

## Problem Statement

The current meeting-centric pages aren't useful:
- 12+ empty sections showing "No agenda items in this section"
- Only 4 actual items buried in procedural noise
- No meeting summary or context
- Meetings are arbitrary collections of unrelated items (employee benefits + sewage spills + bus ads + housing)
- No coherent narrative - just "whatever was ready to vote that week"

**Example:** [meeting 17477](file:///Users/andrewcho/Documents/GitHub/la-council-scraper/site/meetings/17477.html)

## New Direction: Council File Tracking

**Shift focus from meetings to council files**

Instead of "what happened in meeting 17477", provide "the story of council file 25-1294 (Manitou Vistas housing)".

### Why This Makes Sense

- **Continuity:** Track one legislative item through its entire lifecycle
- **User intent:** People care about specific issues ("that housing project near me"), not random meeting snapshots
- **Better navigation:** Browse by district, topic, keyword - not just chronological meetings
- **Actual value:** Follows issues over time vs. official site's single-meeting view

### Architecture

**Primary pages:** Council files (e.g., `councilfiles/25-1294.html`)
- File number and title
- Current status
- District (if applicable)
- Timeline of appearances across meetings
- All related documents/attachments
- AI-generated summary of each PDF attachment
- Links to meetings where discussed

**Secondary pages:** Meetings (simplified)
- Just a landing page with date, video, official agenda link
- Simple list of council files discussed
- Each links to the council file's tracking page

**Additional views:**
- Browse by district
- Browse by topic/committee
- Search by keyword
- Recent activity feed

## Technical Plan: PDF Processing

### Why PDFs Matter

Council file attachments are mostly PDFs containing:
- Committee reports
- Motions
- Budget documents
- Maps, charts, zoning diagrams
- Public comments

These contain the actual substance but are currently just links.

### Claude PDF Support

**Use Claude Haiku 4.5:**
- ✅ Accepts PDFs directly (text + images/charts/tables)
- ✅ 200K context window (handles large documents)
- ✅ Cost: $1 per million input tokens (~$0.05 per 50k token PDF)
- ✅ Fast and capable for document summarization

### Implementation Approach

**During pipeline execution (local machine):**

1. Parse agenda JSON to find attachments
2. For each PDF attachment:
   - Download to memory (not disk): `pdf_content = requests.get(url).content`
   - Send to Claude Haiku API with summarization prompt
   - Receive summary
   - Save summary to `data/pdf_summaries/{historyId}.json`
   - PDF discarded when variable goes out of scope (never stored)

**Data structure:**
```
data/
  agendas/
    agenda_17477.json              # existing meeting data
  pdf_summaries/
    {historyId}.json               # AI summaries keyed by attachment ID
  councilfiles/
    25-1294.json                   # aggregated data per council file
```

**PDF URL pattern:**
```python
base_url = "https://lacity.primegov.com"
attachment_url = "/api/compilemeetingattachmenthistory/historyattachment/?historyId={id}"
full_url = base_url + attachment_url
```

### Smart Filtering

Don't process every attachment - focus on valuable ones:
- ✅ Process: Reports, Motions, Committee Reports, Budget docs
- ❌ Skip: Speaker cards, procedural "Council Action dated..." files

### Execution Model

**Current setup (keep it simple):**
- Run pipeline locally: `python run_pipeline.py`
- Your machine downloads PDFs, processes with Claude API
- Commit generated summaries/HTML to git
- GitHub Pages serves static files (no code execution)

**Future option (not now):**
- GitHub Actions could automate this
- But adds complexity - defer until manual process is tedious

## Next Steps

### 1. Data Exploration
- Analyze existing agenda JSONs
- Count unique council files across all meetings
- Identify council files that appear in multiple meetings (show progression)
- Find "rich" example with multiple attachments for prototyping

### 2. Prototype
- Pick one good example council file
- Download and process one PDF with Haiku
- Validate that summaries are actually useful
- Design one council file page based on real data

### 3. Build System
- Script to aggregate council file data across meetings
- PDF processing pipeline
- Council file page generator
- Simplified meeting page generator

### 4. Iterate
- See what's useful in practice
- Adjust based on real usage
- Add features (search, filtering, etc.) as needed

## Key Principles

- **Lean and iterative:** Don't over-complicate, build what's needed
- **Validate first:** Test with real data before building full system
- **Add value:** Only build features that provide insight beyond official site
- **Keep it simple:** Manual local execution for now, automate later if needed

## Questions to Answer

- [ ] How many council files do we have?
- [ ] How many appear across multiple meetings?
- [ ] What does a typical PDF attachment contain?
- [ ] Are PDF summaries actually more useful than just titles?
- [ ] What metadata can we extract to enable filtering/search?

---

**Resume conversation by:** Running data exploration to understand council file patterns in our existing agenda data.
