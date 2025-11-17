# Data Exploration Results - Council File Analysis

**Date:** 2025-11-16
**Analysis of:** 7 agenda JSON files (meetings 17283, 17367, 17406, 17407, 17432, 17455, 17477)

## Executive Summary

✅ **Council files are the right unit of organization**

- **194 unique council files** across 7 meetings (198 total items, 100% have council file numbers)
- **Only 4 files appear in multiple meetings** - showing legislative progression over time
- **Attachments vary widely:** From 0 to 220 attachments per file
- **Rich examples available** for PDF processing prototypes

---

## Key Findings

### 1. Council File Statistics

| Metric | Value |
|--------|-------|
| Total agenda items analyzed | 198 |
| Items with council file numbers | 198 (100%) |
| Unique council files | 194 |
| Files appearing in 2+ meetings | 4 |
| Average attachments per file | ~6.5 |

### 2. Files Appearing Across Multiple Meetings

These 4 files show legislative progression over time:

#### **25-1084** (Planning/Environmental)
- **Meetings:** 17283, 17407
- **Attachments:** 48 total
- **Subject:** Mitigated Negative Declaration (MND) for a development project
- **Progression:** "Continued consideration" → Final consideration
- **Example attachments:**
  - Report from Planning and Land Use Management Committee
  - Department of City Planning Supplemental Transmittal
  - Environmental documents

#### **25-1294** (Housing - Manitou Vistas) ⭐ **GOOD PROTOTYPE CANDIDATE**
- **Meetings:** 17283, 17477
- **District:** CD 14
- **Attachments:** 7 total
- **Subject:** Sale/change of ownership for Manitou Vistas I & II affordable housing
- **Location:** 3420 & 3414 Manitou Avenue
- **Progression:** Housing Committee report → Council floor consideration
- **Example attachments:**
  - Housing and Homelessness Committee Report
  - Motion (Jurado - Raman) with project details
- **Why good for prototype:**
  - Concrete topic (housing project)
  - Clear geographic location
  - Multiple meeting appearances showing story arc
  - Manageable attachment count for testing

#### **25-1209** (Public Convenience/Licensing)
- **Meetings:** 17283, 17407
- **Attachments:** 16 total
- **Subject:** Application for Determination of Public Convenience or Necessity
- **Progression:** "Continued consideration" → Final hearing

#### **25-0900-S46** (Street Lighting)
- **Meetings:** 17283, 17407
- **Attachments:** 8 total
- **Subject:** Bureau of Street Lighting ordinance
- **Progression:** First consideration → Continued consideration

### 3. Richest Files by Attachment Count

| Rank | Council File | Meetings | Attachments | Subject |
|------|--------------|----------|-------------|---------|
| 1 | 23-1134 | 1 | **220** | Housing economic study & amendments |
| 2 | 25-0030 | 1 | 82 | Emergency declaration resolution |
| 3 | 25-1084 | 2 | 48 | Environmental review (MND) |
| 4 | 13-0332 | 1 | 60 | Convention center agreement |
| 5 | 12-0344 | 1 | 60 | Trade/tourism agreement |

### 4. Attachment Patterns Observed

From examining the JSON structure:

**Attachment pairs:** Each document appears twice in the attachment array:
1. Preview link: `/viewer/preview?id=0&type=8&uid={uuid}` (no historyId)
2. Download link: `/api/compilemeetingattachmenthistory/historyattachment/?historyId={uuid}` (has historyId)

**Smart filtering recommended:**
- ✅ **Process:** Committee reports, motions, department reports, environmental docs
- ⚠️ **Maybe:** Community impact statements, public communications
- ❌ **Skip:** Speaker cards, "Council Action dated..." procedural files, "Attachment" with generic names

**Common attachment types:**
- Committee reports (e.g., "Report from Housing and Homelessness Committee")
- Motions (e.g., "Motion (Jurado - Raman) dated 10-31-25")
- Department reports (e.g., "Report from Bureau of Sanitation")
- Environmental documents (MND, categorical exemptions)
- Prior council actions (procedural history)
- Speaker cards (less substantive)

### 5. Data Structure Observations

**Available metadata per agenda item:**
```json
{
  "item_id": "156427",
  "item_number": "(4)",
  "council_file": "25-1294",
  "district": "CD 14",  // Sometimes present
  "title": "...",
  "recommendation": "...",
  "raw_text": "...",
  "video_location": "9925",
  "mig": "uuid",
  "has_attachments": true,
  "attachments": [...]
}
```

**Key observations:**
- `district` field not always present (only for location-specific items)
- `recommendation` contains fiscal/community impact info
- `raw_text` has original unstructured text
- `video_location` provides timestamp in meeting video
- `mig` appears to be unique identifier

---

## Recommendations for Next Steps

### 1. Best Prototype Candidate: Council File 25-1294 (Manitou Vistas)

**Why this is ideal:**
- ✅ Appears in 2 meetings (shows progression)
- ✅ Concrete, understandable topic (affordable housing sale/ownership change)
- ✅ Geographic location (CD 14, specific addresses)
- ✅ Manageable attachment count (7 total)
- ✅ Mix of document types (committee report + motion)
- ✅ Real-world user interest (housing issues are high-profile)

**Attachments to process:**
- Meeting 17283:
  - `0d2b0c57-a58e-40b6-ad90-336cf8ae0d32` - Housing Committee Report (11-5-25)
  - `67cf4cb4-da48-467b-9781-c5c2e6cb8fc8` - Motion (Jurado - Raman) dated 10-31-25
- Meeting 17477:
  - `7b9facb7-3191-40bd-8b1c-23c7702da1c8` - Motion (Jurado - Raman) dated 10-31-25 (possibly same as above)

### 2. Alternative Candidates

**If 25-1294 doesn't work out:**

**Option A: 24-0887 (Sewer Spill in CD 11)**
- District-specific infrastructure issue
- 12 attachments with clear narrative (incident → investigation → report)
- Appears in 1 meeting but has rich document trail
- Attachments include motion, bureau reports, committee reports

**Option B: 25-1084 (Environmental Review)**
- 48 attachments (great for testing batch processing)
- Appears in 2 meetings
- More technical/complex (good stress test)

### 3. PDF Processing Strategy

**URL Pattern Confirmed:**
```python
base_url = "https://lacity.primegov.com"
attachment_path = "/api/compilemeetingattachmenthistory/historyattachment/"
full_url = f"{base_url}{attachment_path}?historyId={history_id}"
```

**Recommended filtering logic:**
```python
def should_process_attachment(attachment_text):
    """Determine if attachment is worth processing with Claude."""
    skip_patterns = [
        "Speaker Card",
        "Council Action dated",
        "Attachment",  # Generic preview links
    ]
    return not any(pattern in attachment_text for pattern in skip_patterns)
```

### 4. Next Actions

1. **Download prototype PDFs** from council file 25-1294
2. **Test Claude Haiku 4.5** with one PDF to validate summary quality
3. **Design council file page** based on 25-1294 data structure
4. **Build aggregation script** to combine data across meetings
5. **Iterate** based on what's actually useful

---

## Answers to Planning Doc Questions

✅ **How many council files do we have?**
→ 194 unique files across 7 meetings

✅ **How many appear across multiple meetings?**
→ 4 files (2.1% of total)

⏳ **What does a typical PDF attachment contain?**
→ Need to download and inspect (next step)

⏳ **Are PDF summaries actually more useful than just titles?**
→ Need to test with Claude (next step)

⏳ **What metadata can we extract to enable filtering/search?**
→ Council file number, district, title, committee, dates, attachment types

---

## Data Files Generated

- **[data/council_file_analysis.json](../data/council_file_analysis.json)** - Full analysis data for all 194 council files
- **[analyze_council_files.py](../analyze_council_files.py)** - Reusable analysis script

---

**Next:** Test PDF processing with council file 25-1294 attachments
