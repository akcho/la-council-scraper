#!/usr/bin/env python3
"""
Full pipeline: Fetch meetings -> Get transcripts -> Summarize -> Deploy site

Run this to update councilreader.com with new meeting summaries.

Usage:
    python run_pipeline.py              # Full pipeline with deploy
    python run_pipeline.py --no-deploy  # Skip deployment (local testing)
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path


def run_command(cmd, description, allow_fail=False):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        if allow_fail:
            print(f"\n⚠️  Warning: {description} (continuing anyway)")
            return False
        else:
            print(f"\n❌ Error in: {description}")
            sys.exit(1)
    return True


def get_meetings_needing_summaries():
    """Find City Council/Housing meetings with videos but no summaries."""
    if not os.path.exists('recent_meetings.json'):
        return []

    with open('recent_meetings.json') as f:
        meetings = json.load(f)

    # Only process these meeting types
    TARGET_COMMITTEES = {1, 104}  # City Council, Housing Committee

    needs_summary = []
    for m in meetings:
        meeting_id = m['id']
        committee_id = m.get('committeeId')

        # Skip non-target committees
        if committee_id not in TARGET_COMMITTEES:
            continue

        # Skip SAP (Sign Language) meetings
        if 'SAP' in m.get('title', ''):
            continue

        # Check if has video but no summary
        has_video = bool(m.get('videoUrl'))
        summary_file = Path(f"data/video_summaries/meeting_{meeting_id}_summary.json")
        has_summary = summary_file.exists()

        if has_video and not has_summary:
            needs_summary.append(m)

    return needs_summary


def process_meeting(meeting):
    """Download transcript and generate summary for a single meeting."""
    from get_transcripts import get_youtube_transcript
    from summarize_meeting import summarize_with_claude

    meeting_id = meeting['id']
    video_url = meeting.get('videoUrl')
    title = meeting.get('title', 'Meeting')
    date = meeting.get('date', '')

    print(f"\n📋 Processing: {title} ({date})")
    print(f"   Meeting ID: {meeting_id}")
    print(f"   Video: {video_url}")

    # Step 1: Get transcript
    transcript = get_youtube_transcript(video_url)
    if not transcript:
        print(f"   ⚠️  No transcript available (captions may not be ready yet)")
        return False

    # Save transcript
    transcript_dir = Path('data/transcripts')
    transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript_file = transcript_dir / f"meeting_{meeting_id}_transcript.txt"
    with open(transcript_file, 'w') as f:
        f.write(transcript)
    print(f"   ✅ Saved transcript: {len(transcript):,} characters")

    # Step 2: Generate summary
    try:
        full_summary, newsletter_blurb = summarize_with_claude(transcript)
    except Exception as e:
        print(f"   ❌ Summarization failed: {e}")
        return False

    # Save summary to permanent location
    summary_dir = Path('data/video_summaries')
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_file = summary_dir / f"meeting_{meeting_id}_summary.json"

    summary_data = {
        'meeting_id': meeting_id,
        'summary': full_summary,
        'newsletter_blurb': newsletter_blurb,
        'video_url': video_url
    }
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    print(f"   ✅ Saved summary")

    return True


def main():
    """Run the full pipeline."""
    deploy = '--no-deploy' not in sys.argv

    print("=" * 60)
    print("Council Reader - Full Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Fetch latest meetings
    run_command(
        "python fetch_meetings.py",
        "Step 1/5: Fetching latest meetings from PrimeGov"
    )

    # Step 2: Parse agendas
    run_command(
        "python parse_agendas.py",
        "Step 2/5: Parsing meeting agendas"
    )

    # Step 3: Process meetings that need summaries
    print(f"\n{'='*60}")
    print("📋 Step 3/5: Generating summaries for new meetings")
    print(f"{'='*60}\n")

    meetings_to_process = get_meetings_needing_summaries()
    if not meetings_to_process:
        print("No new meetings need summaries.")
    else:
        print(f"Found {len(meetings_to_process)} meeting(s) needing summaries:")
        for m in meetings_to_process:
            print(f"  - {m['id']}: {m.get('title', 'Meeting')} ({m.get('date', '')})")

        summaries_created = 0
        for meeting in meetings_to_process:
            if process_meeting(meeting):
                summaries_created += 1

        print(f"\n✅ Created {summaries_created} summary(ies)")

    # Step 4: Generate site
    run_command(
        "python generate_site.py",
        "Step 4/5: Generating site HTML"
    )

    # Step 5: Deploy (optional)
    if deploy:
        run_command(
            "./deploy.sh",
            "Step 5/5: Deploying to councilreader.com"
        )
    else:
        print(f"\n{'='*60}")
        print("⏭️  Step 5/5: Skipping deployment (--no-deploy)")
        print(f"{'='*60}\n")

    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE!")
    print("=" * 60)

    if deploy:
        print("\n🌐 Site updated at: https://councilreader.com")
    else:
        print("\n📁 Site generated locally in: site/")
        print("   Run ./deploy.sh to push to production")

    print()


if __name__ == "__main__":
    main()
