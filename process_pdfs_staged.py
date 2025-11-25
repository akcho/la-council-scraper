#!/usr/bin/env python3
"""
Staged PDF Processing for Council Files

Processes PDFs with smart filtering and staging:
1. Stage 1: High-value documents (staff reports, findings, appeals, conditions)
2. Stage 2: Sample of "other" documents to assess value
3. Stage 3: Remaining documents (if desired)

Features:
- Smart categorization of document types
- Skips low-value documents (speaker cards, procedural)
- Tracks costs and progress
- Can resume from interruption
"""

import os
import sys
import json
import random
import time
import requests
import io
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from typing import Dict, List, Tuple
from pypdf import PdfReader, PdfWriter

# Force unbuffered output for background processing
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load environment variables
load_dotenv()

# Base URL for PDF downloads
BASE_URL = "https://lacity.primegov.com"

# Output directories
PDF_SUMMARIES_DIR = Path("data/pdf_summaries")
PDF_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

# Document categorization patterns
HIGH_VALUE_PATTERNS = [
    (r"staff report", "staff_report"),
    (r"report from", "staff_report"),
    (r"committee report", "staff_report"),
    (r"appeal", "appeal"),
    (r"findings", "findings"),
    (r"conditions of approval", "conditions"),
    (r"conditions", "conditions"),
]

LOW_VALUE_PATTERNS = [
    (r"proof of publication", "skip_procedural"),
    (r"proof of mailing", "skip_procedural"),
    (r"certificate of posting", "skip_procedural"),
    (r"mailing list", "skip_procedural"),
    (r"returned envelope", "skip_procedural"),
    (r"speaker card", "skip_speaker_cards"),
    (r"www.lacouncilfile.com", "skip_url_link"),
    (r"^noe$", "skip_noe"),
    (r"notice of exemption", "skip_noe"),
]


def categorize_document(text: str) -> Tuple[str, int]:
    """
    Categorize a document based on its title.

    Returns:
        Tuple of (category, priority) where priority is:
        1 = high-value (process immediately)
        2 = medium-value (process in stage 2 sample)
        0 = low-value (skip)
    """
    text_lower = text.lower()

    # Check if it's high-value
    for pattern, category in HIGH_VALUE_PATTERNS:
        if pattern in text_lower:
            return category, 1

    # Check if it's low-value (skip)
    for pattern, category in LOW_VALUE_PATTERNS:
        if pattern in text_lower:
            return category, 0

    # Everything else is medium-value
    return "other", 2


def load_all_attachments() -> List[Dict]:
    """Load all attachments from council files."""
    councilfiles_dir = Path("data/councilfiles")
    all_attachments = []

    for json_file in councilfiles_dir.glob("*.json"):
        if json_file.name == "index.json":
            continue

        with open(json_file) as f:
            data = json.load(f)

        council_file = data["council_file"]

        for attachment in data.get("attachments", []):
            # Skip if already has summary
            if attachment.get("has_summary"):
                continue

            # Add council file context
            attachment["council_file"] = council_file
            all_attachments.append(attachment)

    return all_attachments


def filter_and_stage_documents(attachments: List[Dict], stage: int, sample_size: int = 150) -> List[Dict]:
    """
    Filter documents based on stage.

    Args:
        attachments: List of all attachments
        stage: 1 (high-value only), 2 (sample of other), 3 (all remaining)
        sample_size: Number of "other" docs to sample in stage 2

    Returns:
        List of attachments to process in this stage
    """
    categorized = []

    for attachment in attachments:
        category, priority = categorize_document(attachment.get("title", ""))
        attachment["category"] = category
        attachment["priority"] = priority
        categorized.append(attachment)

    if stage == 1:
        # High-value documents only
        filtered = [a for a in categorized if a["priority"] == 1]
        print(f"\n📊 Stage 1: High-value documents")
        print(f"   Found {len(filtered)} documents to process")

    elif stage == 2:
        # Sample of "other" documents
        other_docs = [a for a in categorized if a["priority"] == 2]
        random.seed(42)  # Reproducible sampling
        filtered = random.sample(other_docs, min(sample_size, len(other_docs)))
        print(f"\n📊 Stage 2: Sample of 'other' documents")
        print(f"   Sampling {len(filtered)} of {len(other_docs)} documents")

    elif stage == 3:
        # All remaining medium-value documents
        filtered = [a for a in categorized if a["priority"] == 2]
        print(f"\n📊 Stage 3: All remaining documents")
        print(f"   Found {len(filtered)} documents to process")

    else:
        raise ValueError(f"Invalid stage: {stage}")

    return filtered


def download_pdf(history_id: str) -> bytes:
    """Download PDF from PrimeGov API."""
    url = f"{BASE_URL}/api/compilemeetingattachmenthistory/historyattachment/?historyId={history_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def extract_first_n_pages(pdf_content: bytes, max_pages: int = 100) -> bytes:
    """
    Extract the first N pages from a PDF.

    Args:
        pdf_content: Original PDF content as bytes
        max_pages: Maximum number of pages to extract (default: 100)

    Returns:
        New PDF content with only the first N pages
    """
    # Read the PDF
    reader = PdfReader(io.BytesIO(pdf_content))

    # If PDF has <= max_pages, return original
    if len(reader.pages) <= max_pages:
        return pdf_content

    # Create a new PDF with only the first max_pages
    writer = PdfWriter()
    for page_num in range(max_pages):
        writer.add_page(reader.pages[page_num])

    # Write to bytes
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer.read()


def summarize_pdf_with_claude(pdf_content: bytes, filename: str, council_file: str, max_retries: int = 3, extract_pages: bool = False) -> Tuple[str, Dict]:
    """
    Send PDF to Claude Haiku 4.5 for summarization with retry logic.

    Args:
        pdf_content: PDF file content as bytes
        filename: Original filename
        council_file: Council file number
        max_retries: Maximum retry attempts for rate limiting
        extract_pages: Whether to extract first 100 pages (for large PDFs)

    Returns:
        Tuple of (summary text, usage stats dict)
    """
    import base64

    client = Anthropic()

    # Keep original content for potential retry
    original_pdf_content = pdf_content

    # Extract first 100 pages if requested
    if extract_pages:
        try:
            reader = PdfReader(io.BytesIO(pdf_content))
            original_pages = len(reader.pages)
            pdf_content = extract_first_n_pages(pdf_content, max_pages=100)
            reader_new = PdfReader(io.BytesIO(pdf_content))
            extracted_pages = len(reader_new.pages)
            print(f"   📑 Extracted {extracted_pages} of {original_pages} pages")
        except Exception as e:
            print(f"   ⚠️  Page extraction failed: {e}")
            # Continue with original content

    prompt = f"""You are analyzing a Los Angeles City Council document for council file {council_file}.

Document name: {filename}

Please provide a concise summary (2-4 paragraphs) that covers:

1. **What is being proposed?** - The main action or recommendation
2. **Why?** - The rationale, background, or problem being addressed
3. **Key details** - Important numbers, dates, locations, or stakeholders
4. **Impact** - Who this affects and how

Focus on information that would help a resident understand what's happening and why it matters.
If this is a motion, explain what the motion is asking for.
If this is a committee report, explain the committee's recommendation and reasoning.
If this is an appeal, explain what is being appealed and the appellant's concerns."""

    # Encode PDF to base64
    pdf_base64 = base64.standard_b64encode(pdf_content).decode('utf-8')

    # Retry logic for rate limiting
    for attempt in range(max_retries):
        try:
            # Create message with PDF attachment
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
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

            # Calculate costs (Haiku 4.5 pricing)
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            input_cost = (input_tokens / 1_000_000) * 1.00
            output_cost = (output_tokens / 1_000_000) * 5.00
            total_cost = input_cost + output_cost

            return summary, {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": total_cost
            }

        except Exception as e:
            error_str = str(e)

            # Check if it's a rate limit error
            if "rate_limit_error" in error_str:
                if attempt < max_retries - 1:
                    # Exponential backoff: 60s, 120s, 240s
                    wait_time = 60 * (2 ** attempt)
                    print(f"   ⏳ Rate limit hit. Waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Final retry failed
                    raise

            # Check if it's a page limit or size error - try page extraction
            elif ("100 PDF pages" in error_str or
                  "request_too_large" in error_str or
                  "prompt is too long" in error_str):

                if not extract_pages:
                    # First time seeing this error - retry with page extraction
                    print(f"   ⚠️  PDF too large ({error_str.split(':')[0]})")
                    print(f"   🔄 Retrying with first 100 pages extracted...")
                    return summarize_pdf_with_claude(original_pdf_content, filename, council_file, max_retries, extract_pages=True)
                else:
                    # Already tried page extraction, still failed
                    raise
            else:
                # Non-recoverable error, don't retry
                raise

    # Should never reach here
    raise Exception("Max retries exceeded")


def save_summary(history_id: str, summary: str, attachment: Dict, usage_stats: Dict):
    """Save PDF summary to JSON file."""
    output_file = PDF_SUMMARIES_DIR / f"{history_id}.json"

    data = {
        "historyId": history_id,
        "council_file": attachment["council_file"],
        "meeting_id": attachment.get("meeting_id"),
        "original_filename": attachment.get("title", ""),
        "category": attachment.get("category", "unknown"),
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


def process_documents(documents: List[Dict], stage: int):
    """Process a list of documents."""

    print(f"\n{'=' * 70}")
    print(f"Processing Stage {stage}")
    print(f"{'=' * 70}")

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return 1

    total_cost = 0.0
    processed = 0
    failed = 0

    for i, attachment in enumerate(documents, 1):
        history_id = attachment["historyId"]
        filename = attachment.get("title", "")
        council_file = attachment["council_file"]

        # Check if already processed
        summary_file = PDF_SUMMARIES_DIR / f"{history_id}.json"
        if summary_file.exists():
            print(f"\n[{i}/{len(documents)}] ⏭️  Skipping {filename} (already processed)")
            continue

        print(f"\n{'─' * 70}")
        print(f"[{i}/{len(documents)}] 📄 {filename}")
        print(f"   Council File: {council_file}")
        print(f"   Category: {attachment.get('category', 'unknown')}")
        print(f"   History ID: {history_id}")
        print(f"{'─' * 70}")

        try:
            # Download PDF
            print(f"   ⬇️  Downloading...")
            pdf_content = download_pdf(history_id)
            print(f"   ✅ Downloaded {len(pdf_content):,} bytes")

            # Summarize with Claude
            print(f"   🤖 Generating summary...")
            summary, usage_stats = summarize_pdf_with_claude(pdf_content, filename, council_file)

            # Save summary
            save_summary(history_id, summary, attachment, usage_stats)

            print(f"   ✅ Summary generated")
            print(f"   💰 Cost: ${usage_stats['cost_usd']:.4f} ({usage_stats['input_tokens']:,} in, {usage_stats['output_tokens']:,} out)")

            total_cost += usage_stats["cost_usd"]
            processed += 1

            # Small delay to avoid rate limiting (50k tokens/min = ~12 seconds between large PDFs)
            time.sleep(2)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
            continue

    print("\n" + "=" * 70)
    print(f"✅ Stage {stage} Complete")
    print(f"   Processed: {processed} documents")
    print(f"   Failed: {failed} documents")
    print(f"   Total cost: ${total_cost:.4f}")
    print("=" * 70)

    return 0


def show_stats(attachments: List[Dict]):
    """Show statistics about documents by category."""
    categorized = []
    for attachment in attachments:
        category, priority = categorize_document(attachment.get("title", ""))
        categorized.append((category, priority))

    from collections import Counter
    category_counts = Counter(cat for cat, _ in categorized)

    print("\n📊 Document Statistics:")
    print("\nHigh-value (Stage 1):")
    for category in ["staff_report", "appeal", "findings", "conditions"]:
        count = category_counts.get(category, 0)
        if count > 0:
            print(f"   {category}: {count}")

    high_value_total = sum(1 for _, p in categorized if p == 1)
    print(f"   TOTAL HIGH-VALUE: {high_value_total}")

    print("\nLow-value (Skip):")
    for category in ["skip_procedural", "skip_speaker_cards", "skip_noe", "skip_url_link"]:
        count = category_counts.get(category, 0)
        if count > 0:
            print(f"   {category}: {count}")

    low_value_total = sum(1 for _, p in categorized if p == 0)
    print(f"   TOTAL LOW-VALUE (SKIP): {low_value_total}")

    print("\nOther (Stage 2 sample):")
    other_count = category_counts.get("other", 0)
    print(f"   other: {other_count}")

    print(f"\nTotal documents: {len(attachments)}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Process PDFs with smart filtering and staging")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3], required=True,
                        help="Processing stage: 1=high-value, 2=sample other, 3=all remaining")
    parser.add_argument("--sample-size", type=int, default=150,
                        help="Number of 'other' docs to sample in stage 2 (default: 150)")
    parser.add_argument("--stats-only", action="store_true",
                        help="Show statistics only, don't process")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt and start processing immediately")

    args = parser.parse_args()

    print("=" * 70)
    print("Staged PDF Processing for Council Files")
    print("=" * 70)

    # Load all attachments
    print("\n📂 Loading council file data...")
    all_attachments = load_all_attachments()
    print(f"   Found {len(all_attachments)} attachments without summaries")

    # Show stats if requested
    if args.stats_only:
        show_stats(all_attachments)
        return 0

    # Filter documents for this stage
    documents = filter_and_stage_documents(all_attachments, args.stage, args.sample_size)

    if not documents:
        print("\n✅ No documents to process in this stage")
        return 0

    # Estimate cost
    cost_per_pdf = 0.0058
    estimated_cost = len(documents) * cost_per_pdf
    print(f"\n💰 Estimated cost: ${estimated_cost:.2f} ({len(documents)} documents × ${cost_per_pdf})")

    # Confirm before proceeding (unless --yes flag)
    if not args.yes:
        response = input("\nProceed with processing? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
    else:
        print("\n🚀 Starting processing (--yes flag provided)...")

    # Process documents
    return process_documents(documents, args.stage)


if __name__ == "__main__":
    exit(main())
