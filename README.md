# LA Council Tracker

Track Los Angeles City Council meetings with AI-powered summaries and structured agenda data. Generates a mobile-first static website and Reddit-formatted summaries.

## Quick Start

### For Reddit Summaries

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set up API key
cp .env.example .env
# Edit .env and add your Anthropic API key from https://console.anthropic.com/

# 3. Run the pipeline
python run_pipeline.py
```

### For Website Deployment

```bash
# Generate and deploy site to GitHub Pages
./deploy.sh
```

## What It Does

- ✅ Fetches LA City Council meetings from PrimeGov API
- ✅ Parses agendas into structured JSON (meeting → sections → items)
- ✅ Downloads YouTube auto-generated transcripts
- ✅ Generates AI summaries using Claude Sonnet 4
- ✅ Builds mobile-first static website with meeting pages
- ✅ Formats summaries for r/losangeles with links to meeting pages
- ✅ Automated deployment to GitHub Pages

## Output

**Structured Data:**
- `data/agendas/agenda_{id}.json` - Parsed agenda with full structure
- `recent_meetings.json` - Meeting metadata from API

**AI Summaries:**
- `meeting_{id}_summary.txt` - AI-generated summary
- `meeting_{id}_reddit_comment.md` - Reddit-formatted post with links

**Static Website:**
- `site/index.html` - Homepage with meeting list
- `site/meetings/{id}.html` - Individual meeting pages
- Deployed to: https://akcho.github.io/la-council-scraper (pending activation)

## Key Commands

```bash
# Run full pipeline (fetch, parse, summarize)
python run_pipeline.py

# Generate static site only
python generate_site.py

# Deploy to GitHub Pages
./deploy.sh

# Show latest Reddit comment
python show_comment.py
```

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide (GitHub Pages, Netlify, Vercel)
- **[docs/TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md)** - Technical details and current focus
- **[docs/SESSION_SUMMARY.md](docs/SESSION_SUMMARY.md)** - Latest session summary
- **[docs/gitignored/WEBSITE_PLANNING.md](docs/gitignored/WEBSITE_PLANNING.md)** - Product roadmap

## Tech Stack

- **API:** LA City PrimeGov API
- **Parsing:** BeautifulSoup4
- **Transcripts:** yt-dlp (YouTube auto-captions)
- **AI:** Claude Sonnet 4 (Anthropic)
- **Site Generator:** Jinja2, Python
- **Hosting:** GitHub Pages (gh-pages branch)
- **Analytics:** Plausible (configurable)
- **Distribution:** Reddit → Static site

## Project Status

**Current Phase:** Week 2 MVP Complete ✅

- Static site generator built and tested
- 7 meeting pages generated
- Deployed to gh-pages branch
- Ready for GitHub Pages activation

**Next Step:** Enable GitHub Pages in repo settings to go live!
