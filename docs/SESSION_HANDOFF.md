# Session Handoff - 2025-11-21

## Current Status

**Site is LIVE and fully functional at https://councilreader.com** ✅

### What Just Happened (Last Hour)

1. **Restored all summary data** - Recovered 471 PDF summaries and 7 video summaries from git history that were lost during initial deployment
2. **Successfully deployed to GitHub Pages** - Site is live with all summaries displaying correctly
3. **Verified deployment** - Checked that video summaries appear on meeting pages and PDF summaries appear on council file pages

### Working Directory State

```
master branch: Clean (all changes committed and pushed)
gh-pages branch: Deployed successfully at f56bb5e
```

All changes are committed. No outstanding work in progress.

## Project Overview

**Council Reader** - Makes LA City Council meetings readable with AI-powered summaries

- **Live site**: https://councilreader.com
- **Repo**: https://github.com/akcho/la-council-scraper
- **Data source**: LA City PrimeGov API

### Key Components

1. **Data pipeline**: Fetch → Parse → Aggregate → Summarize → Generate → Deploy
2. **Static site generator**: Python scripts → Jinja2 templates → HTML
3. **GitHub Pages**: Deployed to gh-pages branch with custom domain
4. **Analytics**: Plausible (plausible.io/councilreader.com)

## Data Directories (IMPORTANT)

These directories are **gitignored** but essential for generation:

- `data/pdf_summaries/` - 471 AI summaries of PDF attachments (COMMITTED to master)
- `data/video_summaries/` - 7 AI summaries of meeting videos (COMMITTED to master)
- `data/councilfiles/` - 194 aggregated council file JSONs (REGENERATED each time, gitignored)
- `data/agendas/` - Raw meeting agenda JSONs from API

**Critical**: Before deploying, always ensure `data/councilfiles/` exists by running:
```bash
python aggregate_council_files.py
```

## Key Scripts

### Generation
- `generate_site.py` - Generates meeting HTML pages from agenda data + video summaries
- `generate_councilfile_pages.py` - Generates council file pages with PDF summaries
- `aggregate_council_files.py` - Creates councilfiles data from agendas + PDF summaries

### Summarization
- `summarize_meeting.py` - Creates video summaries from meeting videos via Claude
- `summarize_pdf.py` - Creates PDF summaries from attachments via Claude (uses claude-3-5-sonnet-20241022)

### Data Fetching
- `fetch_agendas.py` - Fetches recent meeting agendas from PrimeGov API
- `parse_agenda.py` - Parses agenda HTML into structured JSON

### Deployment
- `deploy.sh` - Builds site and deploys to gh-pages branch

## Current Data Stats

- **Meetings**: 7 meetings with full agendas
- **Council files**: 194 unique council files tracked
- **PDF summaries**: 471 summaries (170/194 council files have at least one)
- **Video summaries**: 7 meeting summaries
- **Attachments**: 1,010 total attachments across all meetings

## Known Issues & Quirks

### 1. Deploy Script Behavior
The `deploy.sh` script has a quirk where it stashes changes during branch switching. This can sometimes cause gitignored data directories to disappear. Always run `python aggregate_council_files.py` before deploying to ensure council files data is fresh.

### 2. Data Directory Management
The data directories have different persistence patterns:
- `pdf_summaries/` and `video_summaries/` are committed to master (recovered from git history)
- `councilfiles/` is regenerated each time (gitignored, fast to rebuild)
- `agendas/` is gitignored but fetched from API

### 3. Video Summary Rate Limiting
The `summarize_meeting.py` script calls the Claude API and may hit rate limits with large batches. Videos are processed with 2-hour chunks for better summaries.

### 4. PDF Summary Model
PDF summaries use `claude-3-5-sonnet-20241022` model (hardcoded in summarize_pdf.py line 11). This is intentional - don't change without testing.

## Pre-Launch Checklist (Remaining Tasks)

Based on earlier discussions, here are tasks that were mentioned but not completed:

- [ ] Add more event tracking to Plausible (section expansion, council file clicks, etc.)
- [ ] Add About/Disclaimer section to site
- [ ] Consider adding backend logging for analytics
- [ ] Test on mobile devices for responsiveness
- [ ] Set up Plausible account and verify analytics dashboard access

## File Structure

```
la-council-scraper/
├── data/                      # Data files (most gitignored)
│   ├── agendas/              # Raw meeting JSONs
│   ├── pdf_summaries/        # AI summaries (COMMITTED)
│   ├── video_summaries/      # AI summaries (COMMITTED)
│   ├── councilfiles/         # Aggregated data (gitignored)
│   └── council_file_analysis.json
├── site/                      # Generated HTML (gitignored except CNAME)
│   ├── meetings/
│   ├── councilfiles/
│   ├── index.html
│   └── CNAME                 # Custom domain file
├── templates/                 # Jinja2 templates
│   ├── meeting.html
│   ├── councilfile.html
│   └── index.html
├── docs/                      # Documentation
│   └── logs/                 # Daily work logs
├── generate_site.py           # Main site generator
├── generate_councilfile_pages.py
├── aggregate_council_files.py
├── summarize_meeting.py
├── summarize_pdf.py
├── fetch_agendas.py
├── parse_agenda.py
├── deploy.sh                  # Deployment script
├── site_config.json          # Site configuration
└── requirements.txt

Deployed to:
├── gh-pages branch           # Contains flattened site/ contents
    ├── meetings/
    ├── councilfiles/
    ├── data/                 # Data files copied for reference
    ├── index.html
    └── CNAME
```

## Quick Commands

```bash
# Fetch latest meetings
python fetch_agendas.py

# Generate video summaries (costs API credits)
python summarize_meeting.py

# Generate PDF summaries (costs API credits)
python summarize_pdf.py

# Aggregate council files (ALWAYS run before deploying)
python aggregate_council_files.py

# Generate site locally
python generate_site.py
python generate_councilfile_pages.py

# Deploy to production
./deploy.sh

# Check what's deployed
git show gh-pages:index.html | head -50
curl -s https://councilreader.com | head -50
```

## Important URLs

- **Live site**: https://councilreader.com
- **GitHub repo**: https://github.com/akcho/la-council-scraper
- **GitHub Pages settings**: https://github.com/akcho/la-council-scraper/settings/pages
- **PrimeGov API**: https://lacity.primegov.com/api
- **Plausible analytics**: https://plausible.io/councilreader.com

## Configuration Files

- `site_config.json` - Site name, URL, analytics config
- `.env` - API keys (gitignored, has ANTHROPIC_API_KEY)
- `.gitignore` - Excludes most data files, generated HTML, and secrets

## Next Steps for Future Sessions

1. **Monitor analytics** - Check Plausible dashboard to see if tracking is working
2. **Add more tracking events** - Implement click tracking for attachments, council files, etc.
3. **Create About page** - Add disclaimer about AI-generated content
4. **Fetch more meetings** - Run fetch_agendas.py to get newer meetings
5. **Generate more summaries** - Run summarize scripts for new content (costs API credits)

## Recent Git History

```
8469feb (HEAD -> master, origin/master) Update deploy script and regenerate site files
5667541 Restore PDF and video summaries from git history
43cf136 Remove unnecessary intro sentences from meeting summaries
d0ada15 Standardize heading capitalization to sentence case
1ffa89c Polish UI and improve section header clarity
```

## Notes for Next Claude

- Site is working perfectly - all summaries are live
- DNS is configured correctly (councilreader.com points to GitHub Pages)
- Data recovery was successful - all summaries are safely committed
- Deploy script works but requires data/councilfiles/ to exist first
- No urgent issues - focus on enhancements and new features
- Check docs/logs/2025-11-21.md for detailed session log

**Everything is in a clean, working state. Ready for next session!** ✅
