# LA City Council Meeting Summarizer

AI-powered summaries of LA City Council meetings to help residents stay informed.

## What It Does

1. **Fetches** latest City Council meetings from the official PrimeGov API
2. **Downloads** YouTube auto-generated transcripts
3. **Summarizes** using Claude AI into concise, citizen-friendly summaries
4. **Formats** for posting to r/losangeles daily discussion threads

## Setup

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Up API Key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

Get an API key at: https://console.anthropic.com/

### 3. Run the Pipeline

```bash
source venv/bin/activate
python run_pipeline.py
```

This will:
- Fetch the most recent City Council meeting
- Download the YouTube transcript
- Generate an AI summary
- Output a Reddit-formatted comment ready to post

## Individual Scripts

- `fetch_meetings.py` - Fetch meetings from PrimeGov API
- `get_transcripts.py` - Download YouTube transcripts
- `summarize_meeting.py` - Generate AI summaries
- `run_pipeline.py` - Run all steps at once

## Output

The summary will be saved to:
- `meeting_{id}_summary.txt` - Raw summary
- `meeting_{id}_reddit_comment.md` - Formatted for Reddit

## Usage

After each City Council meeting (Tue/Wed/Fri at 10am):
1. Run `python run_pipeline.py`
2. Copy the generated comment
3. Post to r/losangeles daily discussion thread
4. Gather feedback and iterate!

## Project Goals

**Phase 1:** Manual posting to daily threads (current)
**Phase 2:** Semi-automated with review
**Phase 3:** Request standalone posts from mods
**Phase 4:** Scale to newsletter/website

## Tech Stack

- **Data Source:** LA City PrimeGov API
- **Transcripts:** YouTube auto-captions via yt-dlp
- **AI:** Claude Sonnet 4 (Anthropic)
- **Platform:** Reddit (starting with daily discussion threads)

## Contributing

Feedback welcome! This is a work in progress to make local government more accessible.
