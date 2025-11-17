#!/usr/bin/env python3
"""
PDF Processing Prototype for Council File 25-1294

Tests the workflow:
1. Download PDFs from historyId URLs
2. Send to Claude Haiku 4.5 API for summarization
3. Save summaries to data/pdf_summaries/{historyId}.json

This prototype processes council file 25-1294 (Manitou Vistas Housing Project)
to validate the PDF summarization approach before building full pipeline.
"""

import os
import json
import requests
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base URL for PDF downloads
BASE_URL = "https://lacity.primegov.com"

# PDF attachments for council file 25-1294
# From meeting 17283 (Nov 13, 2025):
PDFS_TO_PROCESS = [
    {
        "historyId": "0d2b0c57-a58e-40b6-ad90-336cf8ae0d32",
        "filename": "Housing Committee Report (11-5-25)",
        "meeting_id": 17283,
        "council_file": "25-1294"
    },
    {
        "historyId": "67cf4cb4-da48-467b-9781-c5c2e6cb8fc8",
        "filename": "Motion (Jurado - Raman) 10-31-25",
        "meeting_id": 17283,
        "council_file": "25-1294"
    },
    # From meeting 17477 (Nov 7, 2025):
    {
        "historyId": "7b9facb7-3191-40bd-8b1c-23c7702da1c8",
        "filename": "Motion (Jurado - Raman) 10-31-25",
        "meeting_id": 17477,
        "council_file": "25-1294"
    }
]

# Ensure output directory exists
OUTPUT_DIR = Path("data/pdf_summaries")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def download_pdf(history_id):
    """
    Download PDF from PrimeGov API.

    Args:
        history_id: The historyId from the attachment URL

    Returns:
        bytes: PDF content in memory (never saved to disk)
    """
    url = f"{BASE_URL}/api/compilemeetingattachmenthistory/historyattachment/?historyId={history_id}"
    print(f"   Downloading from: {url}")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Verify it's a PDF
    content_type = response.headers.get('Content-Type', '')
    if 'pdf' not in content_type.lower():
        print(f"   ⚠️  Warning: Content-Type is '{content_type}', expected PDF")

    print(f"   ✅ Downloaded {len(response.content):,} bytes")
    return response.content


def summarize_pdf_with_claude(pdf_content, filename, council_file):
    """
    Send PDF to Claude Haiku 4.5 for summarization.

    Args:
        pdf_content: PDF bytes in memory
        filename: Human-readable filename for context
        council_file: Council file number (e.g., "25-1294")

    Returns:
        str: AI-generated summary
    """
    import base64

    # Initialize Anthropic client (requires ANTHROPIC_API_KEY env var)
    client = Anthropic()

    prompt = f"""You are analyzing a Los Angeles City Council document for council file {council_file}.

Document name: {filename}

Please provide a concise summary (2-4 paragraphs) that covers:

1. **What is being proposed?** - The main action or recommendation
2. **Why?** - The rationale, background, or problem being addressed
3. **Key details** - Important numbers, dates, locations, or stakeholders
4. **Impact** - Who this affects and how

Focus on information that would help a resident understand what's happening and why it matters.
If this is a motion, explain what the motion is asking for.
If this is a committee report, explain the committee's recommendation and reasoning."""

    print(f"   Sending to Claude Haiku 4.5 API...")

    # Encode PDF to base64
    pdf_base64 = base64.standard_b64encode(pdf_content).decode('utf-8')

    # Create message with PDF attachment
    # Claude API accepts PDFs directly as document content
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",  # Haiku 4.5
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )

    summary = message.content[0].text

    # Extract token usage for cost tracking
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens

    # Haiku 4.5 pricing (as of Nov 2024):
    # Input: $1 per million tokens
    # Output: $5 per million tokens
    input_cost = (input_tokens / 1_000_000) * 1.00
    output_cost = (output_tokens / 1_000_000) * 5.00
    total_cost = input_cost + output_cost

    print(f"   ✅ Summary generated")
    print(f"   📊 Tokens: {input_tokens:,} in, {output_tokens:,} out")
    print(f"   💰 Cost: ${total_cost:.4f}")

    return summary, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": total_cost
    }


def save_summary(history_id, summary, metadata, usage_stats):
    """
    Save PDF summary to JSON file.

    Args:
        history_id: The historyId (used as filename)
        summary: The AI-generated summary text
        metadata: Original PDF metadata (filename, meeting, etc.)
        usage_stats: Token usage and cost information
    """
    output_file = OUTPUT_DIR / f"{history_id}.json"

    data = {
        "historyId": history_id,
        "council_file": metadata["council_file"],
        "meeting_id": metadata["meeting_id"],
        "original_filename": metadata["filename"],
        "summary": summary,
        "processing": {
            "model": "claude-haiku-4-5-20251001",
            "input_tokens": usage_stats["input_tokens"],
            "output_tokens": usage_stats["output_tokens"],
            "cost_usd": usage_stats["cost_usd"]
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"   💾 Saved to: {output_file}")


def main():
    """Process all PDFs for council file 25-1294."""

    print("=" * 70)
    print("PDF Processing Prototype - Council File 25-1294")
    print("Manitou Vistas Housing Project")
    print("=" * 70)

    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("   Please set your API key:")
        print("   export ANTHROPIC_API_KEY=your_key_here")
        return 1

    total_cost = 0.0
    processed = 0

    for pdf_info in PDFS_TO_PROCESS:
        history_id = pdf_info["historyId"]
        filename = pdf_info["filename"]

        print(f"\n{'─' * 70}")
        print(f"📄 Processing: {filename}")
        print(f"   History ID: {history_id}")
        print(f"   Meeting: {pdf_info['meeting_id']}")
        print(f"{'─' * 70}")

        try:
            # Step 1: Download PDF to memory
            pdf_content = download_pdf(history_id)

            # Step 2: Summarize with Claude
            summary, usage_stats = summarize_pdf_with_claude(
                pdf_content,
                filename,
                pdf_info["council_file"]
            )

            # Step 3: Save summary
            save_summary(history_id, summary, pdf_info, usage_stats)

            total_cost += usage_stats["cost_usd"]
            processed += 1

            print(f"\n✅ Successfully processed {filename}")

        except Exception as e:
            print(f"\n❌ Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n" + "=" * 70)
    print(f"✅ PROTOTYPE COMPLETE")
    print(f"   Processed: {processed}/{len(PDFS_TO_PROCESS)} PDFs")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Output directory: {OUTPUT_DIR}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
