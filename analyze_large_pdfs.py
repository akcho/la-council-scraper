import json
from pathlib import Path

# Load council files to get document metadata
councilfiles_dir = Path('data/councilfiles')
index_file = councilfiles_dir / 'index.json'

with open(index_file) as f:
    index = json.load(f)

# Track failures by type
failures = {
    'page_limit': [],      # >100 pages
    'request_too_large': [], # >32MB base64
    'token_limit': [],     # >200k tokens
}

# Map error patterns from log
error_map = {
    '18/348': ('25-0600-S126', 4455190, 'page_limit'),
    '48/348': ('25-1191', 3796766, 'page_limit'),
    '76/348': ('25-1217', 4206628, 'page_limit'),
    '91/348': ('25-1108', 13913808, 'page_limit'),
    '125/348': ('23-1134', 10824496, 'page_limit'),
    '132/348': ('25-0987', 10993029, 'page_limit'),
    '163/348': ('22-0032-S1', 1921024, 'page_limit'),
    '170/348': ('21-1330', 5631404, 'page_limit'),
    '276/348': ('21-0748', 5865803, 'page_limit'),
    '277/348': ('21-0748', 7352057, 'page_limit'),
    '278/348': ('21-0748', 1630145, 'page_limit'),
    '279/348': ('21-0748', 2045812, 'page_limit'),
    '280/348': ('21-0748', 6164861, 'page_limit'),
    '281/348': ('21-0748', 6459771, 'page_limit'),
    
    '16/348': ('25-1037', 140022975, 'request_too_large'),
    '131/348': ('25-0987', 71510777, 'request_too_large'),
    '165/348': ('21-1330', 57800151, 'request_too_large'),
    '166/348': ('21-1330', 57540531, 'request_too_large'),
    '168/348': ('21-1330', 112440767, 'request_too_large'),
    '171/348': ('21-1330', 62668708, 'request_too_large'),
    '184/348': ('25-1084', 26171162, 'request_too_large'),
    '190/348': ('25-1084', 26171162, 'request_too_large'),
    '216/348': ('25-1009', 38262769, 'request_too_large'),
    '234/348': ('20-0504', 26600816, 'request_too_large'),
    '252/348': ('23-0494-S2', 35110268, 'request_too_large'),
    
    '232/348': ('12-0344', 6824318, 'token_limit'),
}

print("=" * 90)
print("LARGE PDF FAILURE ANALYSIS")
print("=" * 90)
print()

# Summary by type
for error_type, docs in [
    ('page_limit', 'PDF exceeds 100 pages (API limit)'),
    ('request_too_large', 'File too large (>32MB base64)'),
    ('token_limit', 'Content exceeds 200k tokens'),
]:
    count = sum(1 for k, v in error_map.items() if v[2] == error_type)
    print(f"{error_type.upper():20} {count:3} docs  |  {docs}")

print()
print("=" * 90)
print("POTENTIAL SOLUTIONS")
print("=" * 90)
print()

print("Option 1: SKIP THEM")
print("-" * 90)
print("  Pros: Simple, no cost")
print("  Cons: Missing ~27 high-value documents")
print("  Impact: ~8% of Stage 1 docs (27/348)")
print()

print("Option 2: EXTRACT FIRST 100 PAGES (for page_limit errors)")
print("-" * 90)
print("  Pros: Get most of the content")
print("  Cons: Miss later sections, requires PyPDF2/pypdf")
print("  Impact: Handles 14 docs (page_limit only)")
print("  Cost: ~$0.08 (14 docs × ~$0.006)")
print()

print("Option 3: SMART EXTRACTION (first 50 + last 50 pages)")
print("-" * 90)
print("  Pros: Get intro + conclusion")
print("  Cons: Miss middle content, more complex")
print("  Impact: Handles 14 docs (page_limit only)")
print()

print("Option 4: USE CLAUDE.AI WEB (manual)")
print("-" * 90)
print("  Pros: Can handle larger files via web interface")
print("  Cons: Manual work, not scalable")
print("  Impact: Could handle some docs")
print()

print("Option 5: HYBRID - Extract pages for some, skip truly massive ones")
print("-" * 90)
print("  Pros: Best cost/benefit tradeoff")
print("  Cons: Some manual decision making")
print("  Details:")
print("    - page_limit (14 docs): Extract first 100 pages → ~$0.08")
print("    - token_limit (1 doc): Try extracting first 100 pages → ~$0.006")
print("    - request_too_large (11 docs): Skip or manual review → $0")
print("  Total cost: ~$0.09")
print()

print("=" * 90)
print("RECOMMENDATION: Option 5 (Hybrid)")
print("=" * 90)
print()
print("Next steps:")
print("  1. Install pypdf: pip install pypdf")
print("  2. Add page extraction to process_pdfs_staged.py")
print("  3. Re-run failed docs with extraction enabled")
print("  4. Manually review the 11 truly massive files (26-140MB)")
print()
print("Files to extract (page_limit + token_limit): 15 docs")
print("Files to skip (request_too_large): 11 docs")
print()

