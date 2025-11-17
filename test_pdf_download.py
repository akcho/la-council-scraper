#!/usr/bin/env python3
"""
Test PDF download without requiring API key.
This validates that we can fetch PDFs from PrimeGov before processing them.
"""

import requests

BASE_URL = "https://lacity.primegov.com"

# Test PDFs from council file 25-1294
TEST_PDFS = [
    {
        "historyId": "0d2b0c57-a58e-40b6-ad90-336cf8ae0d32",
        "filename": "Housing Committee Report (11-5-25)",
    },
    {
        "historyId": "67cf4cb4-da48-467b-9781-c5c2e6cb8fc8",
        "filename": "Motion (Jurado - Raman) 10-31-25 [Meeting 17283]",
    },
    {
        "historyId": "7b9facb7-3191-40bd-8b1c-23c7702da1c8",
        "filename": "Motion (Jurado - Raman) 10-31-25 [Meeting 17477]",
    }
]

def test_download(history_id, filename):
    """Test downloading a PDF."""
    url = f"{BASE_URL}/api/compilemeetingattachmenthistory/historyattachment/?historyId={history_id}"

    print(f"\n{'─' * 70}")
    print(f"📄 Testing: {filename}")
    print(f"   History ID: {history_id}")
    print(f"{'─' * 70}")
    print(f"   URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        size = len(response.content)

        print(f"   ✅ Status: {response.status_code}")
        print(f"   Content-Type: {content_type}")
        print(f"   Size: {size:,} bytes")

        # Verify it's a PDF
        if response.content.startswith(b'%PDF'):
            print(f"   ✅ Valid PDF file")
            return True
        else:
            print(f"   ⚠️  Warning: Not a PDF file")
            print(f"   First 50 bytes: {response.content[:50]}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("=" * 70)
    print("PDF Download Test - Council File 25-1294")
    print("=" * 70)

    results = []
    for pdf in TEST_PDFS:
        success = test_download(pdf["historyId"], pdf["filename"])
        results.append(success)

    print("\n" + "=" * 70)
    print(f"✅ Results: {sum(results)}/{len(results)} PDFs downloaded successfully")
    print("=" * 70)

    if all(results):
        print("\n🎉 All PDFs downloaded successfully!")
        print("Next step: Set up API key and run process_pdfs_prototype.py")
        print("See PDF_PROCESSING_README.md for instructions")
    else:
        print("\n⚠️  Some PDFs failed to download")

    return 0 if all(results) else 1

if __name__ == "__main__":
    exit(main())
