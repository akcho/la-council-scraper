#!/bin/bash
# Daily update script for running on local Mac (instead of GitHub Actions)
#
# Setup on old MacBook:
# 1. Clone repo: git clone https://github.com/akcho/la-council-scraper.git
# 2. cd la-council-scraper
# 3. python3 -m venv venv && source venv/bin/activate
# 4. pip install -r requirements.txt
# 5. brew install yt-dlp (or pip install yt-dlp)
# 6. cp .env.example .env && edit .env with your ANTHROPIC_API_KEY
# 7. Set up SSH key for GitHub push access
# 8. Install launchd plist (see com.councilreader.daily-update.plist)

set -e

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Log file
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/update_$(date '+%Y-%m-%d_%H%M%S').log"

# Redirect all output to log
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "Council Reader Daily Update"
echo "Started: $(date)"
echo "========================================"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "ERROR: venv not found. Run: python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "ERROR: .env file not found"
    exit 1
fi

# Pull latest changes
echo ""
echo "Pulling latest changes..."
git pull origin master

# Fetch latest meetings
echo ""
echo "Fetching meetings..."
python fetch_meetings.py

# Find new meetings to process
echo ""
echo "Checking for new meetings..."

NEW_MEETINGS=$(python -c "
import json
import os

with open('recent_meetings.json') as f:
    meetings = json.load(f)

processed_file = 'data/processed_meetings.txt'
processed = set()
if os.path.exists(processed_file):
    with open(processed_file) as f:
        processed = set(line.strip() for line in f if line.strip())

TARGET_TYPES = ['City Council Meeting', 'Housing and Homelessness Committee']

new_meetings = []
for m in meetings:
    title = m.get('title', '')
    is_target = any(title == t or (title.startswith(t + ' -') and 'SAP' not in title and 'SPECIAL' not in title) for t in TARGET_TYPES)

    if m.get('videoUrl') and str(m['id']) not in processed and is_target:
        new_meetings.append(str(m['id']))

print(','.join(new_meetings))
")

if [ -z "$NEW_MEETINGS" ]; then
    echo "No new meetings to process"
    echo ""
    echo "Finished: $(date)"
    exit 0
fi

echo "New meetings to process: $NEW_MEETINGS"

# Parse agendas
echo ""
echo "Parsing agendas..."
python parse_agendas.py

# Process each meeting
IFS=',' read -ra MEETING_IDS <<< "$NEW_MEETINGS"
PROCESSED_COUNT=0

for meeting_id in "${MEETING_IDS[@]}"; do
    echo ""
    echo "=========================================="
    echo "Processing meeting $meeting_id"
    echo "=========================================="

    # Download transcript
    echo "Downloading transcript..."
    python -c "
import json
from get_transcripts import get_youtube_transcript

with open('recent_meetings.json') as f:
    meetings = json.load(f)

meeting = next((m for m in meetings if str(m['id']) == '$meeting_id'), None)
if meeting and meeting.get('videoUrl'):
    transcript = get_youtube_transcript(meeting['videoUrl'])
    if transcript:
        with open(f'data/transcripts/meeting_{meeting[\"id\"]}_transcript.txt', 'w') as f:
            f.write(transcript)
        print(f'Saved transcript ({len(transcript):,} chars)')
    else:
        print('No transcript available')
        exit(1)
" || { echo "Failed to get transcript for $meeting_id, skipping"; continue; }

    # Generate summary
    echo "Generating summary..."
    python -c "
import json
import os
from summarize_meeting import summarize_with_claude

meeting_id = '$meeting_id'
transcript_file = f'data/transcripts/meeting_{meeting_id}_transcript.txt'

if not os.path.exists(transcript_file):
    print('No transcript file')
    exit(1)

with open('recent_meetings.json') as f:
    meetings = json.load(f)

meeting = next((m for m in meetings if str(m['id']) == meeting_id), None)
if not meeting:
    exit(1)

with open(transcript_file) as f:
    transcript = f.read()

full_summary, newsletter_blurb = summarize_with_claude(transcript)
if full_summary:
    os.makedirs('data/video_summaries', exist_ok=True)
    summary_data = {
        'meeting_id': int(meeting_id),
        'video_url': meeting.get('videoUrl'),
        'summary': full_summary,
        'newsletter_blurb': newsletter_blurb,
        'transcript_length': len(transcript)
    }
    with open(f'data/video_summaries/meeting_{meeting_id}_summary.json', 'w') as f:
        json.dump(summary_data, f, indent=2)
    print('Summary saved')
" || { echo "Failed to generate summary for $meeting_id, skipping"; continue; }

    # Mark as processed
    mkdir -p data
    echo "$meeting_id" >> data/processed_meetings.txt

    PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
    echo "Completed meeting $meeting_id"
done

if [ $PROCESSED_COUNT -eq 0 ]; then
    echo ""
    echo "No meetings were successfully processed"
    echo "Finished: $(date)"
    exit 0
fi

# Generate site
echo ""
echo "Generating site..."
python generate_site.py
python aggregate_council_files.py
python generate_councilfile_pages.py

# Commit changes to master
echo ""
echo "Committing changes..."
git add data/processed_meetings.txt data/video_summaries/ data/transcripts/ data/agendas/
git commit -m "Add summaries for $PROCESSED_COUNT meeting(s)" || echo "No changes to commit"
git push origin master || echo "Failed to push to master"

# Deploy to gh-pages
echo ""
echo "Deploying to gh-pages..."
./deploy.sh

echo ""
echo "========================================"
echo "Finished: $(date)"
echo "Processed $PROCESSED_COUNT meeting(s)"
echo "Site: https://councilreader.com"
echo "========================================"

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "update_*.log" -mtime +30 -delete 2>/dev/null || true
