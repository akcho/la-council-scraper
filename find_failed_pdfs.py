import json
from pathlib import Path

# Parse the retry log to find failed documents
with open('pdf_processing_retry.log', 'r') as f:
    log_lines = f.readlines()

failed_docs = []
current_doc = None

for i, line in enumerate(log_lines):
    # Look for document headers
    if line.strip().startswith('[') and '📄' in line:
        current_doc = {
            'title': line.split('📄')[1].strip() if '📄' in line else 'Unknown',
            'position': line.split(']')[0].strip('[')
        }
    elif current_doc and 'Council File:' in line:
        current_doc['council_file'] = line.split('Council File:')[1].strip()
    elif current_doc and 'History ID:' in line:
        current_doc['history_id'] = line.split('History ID:')[1].strip()
    elif current_doc and '❌ Error:' in line:
        current_doc['error'] = line.strip()
        failed_docs.append(current_doc)
        current_doc = None

# Load council file data to get PDF URLs
councilfiles_dir = Path('data/councilfiles')

print("FAILED DOCUMENTS WITH PDF LINKS")
print("=" * 100)
print()

# Group by error type
by_error = {}
for doc in failed_docs:
    error = doc['error']
    if 'prompt is too long' in error:
        error_type = 'prompt_too_long'
    elif 'request_too_large' in error:
        error_type = 'request_too_large'
    elif 'Could not process' in error:
        error_type = 'corrupt'
    else:
        error_type = 'other'
    
    if error_type not in by_error:
        by_error[error_type] = []
    by_error[error_type].append(doc)

# Show examples from each category
for error_type in ['request_too_large', 'prompt_too_long', 'corrupt']:
    if error_type not in by_error:
        continue
    
    docs = by_error[error_type]
    print(f"\n{error_type.upper().replace('_', ' ')} ({len(docs)} documents)")
    print("-" * 100)
    
    # Show first 3 examples
    for doc in docs[:3]:
        history_id = doc.get('history_id', 'unknown')
        title = doc.get('title', 'Unknown')
        cf = doc.get('council_file', 'Unknown')
        
        # Generate PDF URL
        pdf_url = f"https://lacity.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId={history_id}"
        
        print(f"\nCouncil File: {cf}")
        print(f"Title: {title}")
        print(f"PDF URL: {pdf_url}")
    
    if len(docs) > 3:
        print(f"\n... and {len(docs) - 3} more similar documents")

print("\n" + "=" * 100)
print("\nNOTE: These PDFs can be downloaded directly from the URLs above.")
print("They're too large for automated processing but can be viewed manually.")
