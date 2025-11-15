# LA City Council Meeting Summarizer

Automated tool that fetches LA City Council meetings, downloads transcripts, and generates AI-powered summaries for r/losangeles.

## Quick Start

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set up API key
cp .env.example .env
# Edit .env and add your Anthropic API key from https://console.anthropic.com/

# 3. Run the pipeline
./summarize.sh
```

This fetches the latest meeting, downloads the transcript, generates an AI summary, and outputs a Reddit-formatted comment.

## What It Does

- ✅ Fetches LA City Council meetings from PrimeGov API
- ✅ Downloads YouTube auto-generated transcripts
- ✅ Generates AI summaries using Claude Sonnet 4
- ✅ Formats summaries for r/losangeles posts
- 🚧 Parses agenda items into structured data (in progress)
- 🚧 Generates static website with meeting pages (planned)

## Output

Generated files:
- `meeting_{id}_summary.txt` - AI-generated summary
- `meeting_{id}_reddit_comment.md` - Reddit-formatted post

## Development

See [docs/TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md) for technical details and current development focus.

See [docs/gitignored/WEBSITE_PLANNING.md](docs/gitignored/WEBSITE_PLANNING.md) for product roadmap and vision.

## Tech Stack

- **API:** LA City PrimeGov API
- **Transcripts:** yt-dlp (YouTube auto-captions)
- **AI:** Claude Sonnet 4 (Anthropic)
- **Distribution:** Reddit → Static site (planned)
