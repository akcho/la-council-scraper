# Show the 11 request_too_large files with council file context
massive = [
    ('25-1037', 140022975, 'Attachment to Report dated 9-03-25 - Staff Report'),
    ('25-0987', 71510777, 'Attachment to Communication dated 9-03-25 - Staff Report'),
    ('21-1330', 57800151, 'Report from City Administrative Officer dated 10-16-25'),
    ('21-1330', 57540531, 'Report from City Administrative Officer dated 11-21-24'),
    ('21-1330', 112440767, 'Report from City Administrative Officer dated 8-15-23.pdf'),
    ('21-1330', 62668708, 'Report from City Administrative Officer dated 11-02-21.pdf'),
    ('25-1084', 26171162, 'Attachment to Report dated 9-16-25 - Staff Report (1)'),
    ('25-1084', 26171162, 'Attachment to Report dated 9-16-25 - Staff Report (2)'),
    ('25-1009', 38262769, 'Attachment to Report Dated 8-18-25 - Staff Report.pdf'),
    ('20-0504', 26600816, 'Report from Bureaus of Engineering, Street Services, and C...'),
    ('23-0494-S2', 35110268, 'Report from Board of Public Works dated 9-22-25'),
]

import json
from pathlib import Path

councilfiles_dir = Path('data/councilfiles')

print("=" * 100)
print("11 TRULY MASSIVE FILES (26-140 MB) - TOO LARGE FOR API")
print("=" * 100)
print()

for cf_num, size_bytes, title in massive:
    size_mb = size_bytes / 1024 / 1024
    
    # Try to load council file for context
    cf_file = councilfiles_dir / f"{cf_num}.json"
    if cf_file.exists():
        with open(cf_file) as f:
            cf_data = json.load(f)
        cf_title = cf_data.get('title', 'Unknown')[:60]
    else:
        cf_title = "Unknown"
    
    print(f"Council File: {cf_num:15} | {size_mb:6.1f} MB")
    print(f"  CF Title: {cf_title}")
    print(f"  Doc: {title[:70]}")
    print()

print("=" * 100)
print("NOTES:")
print("=" * 100)
print("- These files are 26-140 MB (too large for Claude API)")
print("- Even extracting 100 pages might exceed limits")
print("- Most are comprehensive reports with extensive appendices")
print("- Options:")
print("  1. Skip entirely (acceptable - only 11 docs out of 348)")
print("  2. Try page extraction and see what happens")
print("  3. Manual review via Claude.ai web (upload file directly)")
print("  4. Extract text only (no images) to reduce size")
