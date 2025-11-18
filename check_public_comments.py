import json
from pathlib import Path

# The 600-page report was council file 25-1037
cf_num = "25-1037"

# Load the council file
cf_file = Path(f"data/councilfiles/{cf_num}.json")
with open(cf_file) as f:
    cf_data = json.load(f)

print(f"Council File: {cf_num}")
print(f"Title: {cf_data.get('title', 'Unknown')}")
print("\n" + "=" * 80)
print(f"DOCUMENTS FOR THIS FILE ({len(cf_data.get('attachments', []))} total)")
print("=" * 80)

# Check all attachments
for i, att in enumerate(cf_data.get('attachments', []), 1):
    title = att.get('text', 'Unknown')
    history_id = att.get('historyId', 'Unknown')
    
    # Check if it has a summary
    summary_file = Path(f"data/pdf_summaries/{history_id}.json")
    has_summary = summary_file.exists()
    
    # Check for public comment indicators
    is_comment_related = any(keyword in title.lower() for keyword in [
        'comment', 'letter', 'communication', 'email', 'public', 
        'speaker', 'testimony', 'opposition', 'support'
    ])
    
    status = "✅ SUMMARIZED" if has_summary else "❌ NO SUMMARY"
    marker = "📧" if is_comment_related else "📄"
    
    print(f"\n{i}. {marker} {title}")
    print(f"   {status}")
    
    if is_comment_related:
        print(f"   ⚠️  POSSIBLE PUBLIC COMMENTS!")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

# Count document types
attachments = cf_data.get('attachments', [])
comment_related = [a for a in attachments if any(k in a.get('text', '').lower() 
                   for k in ['comment', 'letter', 'communication', 'email', 'public', 'speaker'])]
                   
print(f"\nTotal documents: {len(attachments)}")
print(f"Possibly comment-related: {len(comment_related)}")

if comment_related:
    print("\nComment-related documents:")
    for att in comment_related:
        history_id = att.get('historyId')
        summary_file = Path(f"data/pdf_summaries/{history_id}.json")
        status = "✅" if summary_file.exists() else "❌"
        print(f"  {status} {att.get('text')}")
else:
    print("\n⚠️  No standalone public comment documents found.")
    print("Public comments are likely embedded in larger staff reports.")

