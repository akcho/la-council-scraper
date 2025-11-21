# Council Reader

Making Los Angeles City Council meetings readable and accessible with AI-powered summaries.

## Overview

This project creates an easy way for people to read up on LA City Council meetings. It builds:

- **Meeting pages** with structured agendas, video links, and AI-generated summaries
- **Council file pages** that track individual issues across multiple meetings
- **Document summaries** using AI to explain bureaucratic PDFs in plain language

The end result is a mobile-first static website that makes city council proceedings accessible to regular people.

## Quick Start

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set up API key
cp .env.example .env
# Edit .env and add your Anthropic API key

# 3. Run the pipeline
python run_pipeline.py                    # Fetch and process data
python generate_site.py                   # Generate meeting pages
python generate_councilfile_pages.py      # Generate council file pages

# 4. Deploy
./deploy.sh
```

## Project Structure

```
la-council-scraper/
├── data/                      # Processed data (git-ignored)
│   ├── agendas/              # Parsed meeting agendas (JSON)
│   ├── councilfiles/         # Aggregated council file data (JSON)
│   ├── pdf_summaries/        # AI summaries of PDF attachments
│   └── video_summaries/      # AI summaries of meeting videos
├── site/                      # Generated static website
│   ├── meetings/             # Individual meeting pages
│   └── councilfiles/         # Council file detail pages
├── templates/                 # Jinja2 templates for HTML generation
│   ├── index.html
│   └── meeting.html
└── [Python scripts]          # Pipeline and utility scripts
```

## How It Works

### The Data Pipeline

1. **Fetch meetings** (`fetch_meetings.py`)
   - Scrapes LA City PrimeGov API for recent meetings
   - Saves metadata to `recent_meetings.json`

2. **Parse agendas** (`parse_agendas.py`)
   - Downloads HTML agendas from PrimeGov portal
   - Extracts structured data: sections, items, council files, attachments
   - Saves to `data/agendas/agenda_{meeting_id}.json`

3. **Aggregate council files** (`aggregate_council_files.py`)
   - Combines data across all meetings for each unique council file
   - Tracks timeline of appearances
   - Links PDF summaries to attachments
   - Saves to `data/councilfiles/{council_file_number}.json`

4. **Generate AI summaries**
   - **PDFs** (`process_pdfs_staged.py`): Downloads and summarizes attachments using Claude API
   - **Videos** (`generate_video_summaries.py`): Downloads transcripts and generates meeting summaries
   - Saves to `data/pdf_summaries/` and `data/video_summaries/`

5. **Build website** (`generate_site.py` and `generate_councilfile_pages.py`)
   - Generates mobile-first HTML pages using Jinja2 templates
   - Creates meeting pages with collapsible sections and AI summaries
   - Creates council file pages with timelines and document summaries

6. **Deploy** (`deploy.sh`)
   - Publishes site to GitHub Pages

### Page Organization

**Meeting pages** (`site/meetings/{meeting_id}.html`):
- Meeting metadata (date, time, video link)
- AI-generated video summary
- Collapsible sections with agenda items
- Inline AI summaries for items with council files
- Links to council file detail pages

**Council file pages** (`site/councilfiles/{council_file_number}.html`):
- File metadata (number, title, district)
- Brief AI summary
- Timeline showing appearances across meetings (most recent first)
- Related documents with AI summaries
- Clickable links back to specific meetings

## Key Scripts

### Main Pipeline
- `run_pipeline.py` - Orchestrates the full pipeline from fetching to summarization
- `generate_site.py` - Generates meeting pages and homepage
- `generate_councilfile_pages.py` - Generates council file detail pages
- `deploy.sh` - Deploys to GitHub Pages

### Data Collection
- `fetch_meetings.py` - Fetches meeting metadata from PrimeGov API
- `parse_agenda.py` - Parses individual meeting agenda HTML
- `parse_agendas.py` - Batch processes all meeting agendas

### Data Processing
- `aggregate_council_files.py` - Combines council file data across meetings
- `process_pdfs_staged.py` - Downloads and summarizes PDF attachments
- `get_transcripts.py` - Downloads YouTube transcripts
- `summarize_meeting.py` - Generates AI summaries of meetings
- `generate_video_summaries.py` - Batch processes video summaries

### Utilities
- `analyze_council_files.py` - Analyzes council file patterns
- `analyze_failures.py` - Reviews PDF processing failures
- `check_new.py` - Checks for new meetings

## Data Models

### Agenda Structure
Defined in `agenda_schema.json`:
```
Meeting
├── meeting_id, template_id
├── meeting_datetime, video_url
└── sections[]
    ├── section_id, title
    └── items[]
        ├── item_id, item_number
        ├── council_file (e.g., "25-1209")
        ├── district (e.g., "CD 12")
        ├── title, recommendation
        └── attachments[]
            └── text, url, historyId
```

### Council File Structure
```
Council File
├── council_file, title, district
├── appearances[] (timeline of meetings)
│   └── meeting_id, date, section, recommendation
├── attachments[]
│   ├── historyId, text, url
│   └── summary (AI-generated from PDF)
├── first_seen, last_seen
└── stats (appearances, attachments, summaries)
```

## Technology Stack

- **Python 3.13** - Core language
- **BeautifulSoup4** - HTML parsing
- **Anthropic Claude API** - AI summarization (Sonnet 4)
- **Jinja2** - HTML templating
- **yt-dlp** - YouTube transcript downloads
- **GitHub Pages** - Static site hosting

## Configuration

**Site Config** (`site_config.json`):
- Site name and URL
- Analytics configuration (Plausible)

**Environment Variables** (`.env`):
- `ANTHROPIC_API_KEY` - Required for AI summarization

## Current Status

**Data Scale:**
- 7 meetings tracked
- 194 council files
- 470+ PDF summaries
- 7 video summaries

**Recent Improvements (November 2025):**
- Made meeting sections collapsible (default: collapsed)
- Redesigned council file timeline with clean meeting cards
- Fixed timeline sorting (most recent meetings first)
- Removed "AI" badges for cleaner UI
- Improved section headers with plain language
- Enhanced markdown formatting in summaries

## Design Principles

1. **Mobile-first** - All pages designed for phone screens first
2. **Plain language** - Bureaucratic jargon replaced with clear titles
3. **AI transparency** - Summaries clearly marked (but not obtrusive)
4. **Progressive disclosure** - Collapsible sections, expandable details
5. **Fast loading** - Static HTML, no JavaScript frameworks
6. **Accessibility** - Semantic HTML, readable fonts, good contrast

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
- **[docs/TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md)** - Technical details
- **[docs/SESSION_SUMMARY.md](docs/SESSION_SUMMARY.md)** - Latest session summary
- **[docs/gitignored/WEBSITE_PLANNING.md](docs/gitignored/WEBSITE_PLANNING.md)** - Product roadmap

## License

MIT License - See LICENSE file for details
