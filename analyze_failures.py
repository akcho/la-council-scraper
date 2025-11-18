import re

# Parse the log file
with open('pdf_processing.log', 'r') as f:
    log_content = f.read()

# Find all failed documents
failures = []
lines = log_content.split('\n')
i = 0
while i < len(lines):
    if '❌' in lines[i]:
        # Look backwards for document info
        doc_info = {}
        for j in range(i-10, i):
            if j >= 0:
                if lines[j].strip().startswith('['):
                    doc_info['title'] = lines[j].strip()
                elif 'Council File:' in lines[j]:
                    doc_info['file'] = lines[j].split('Council File:')[1].strip()
                elif '✅ Downloaded' in lines[j]:
                    bytes_str = lines[j].split('Downloaded')[1].strip().split()[0]
                    doc_info['bytes'] = bytes_str.replace(',', '')
        
        # Get error type
        if '100 PDF pages' in lines[i]:
            doc_info['error'] = 'page_limit'
        elif 'request_too_large' in lines[i]:
            doc_info['error'] = 'request_too_large'
        elif 'prompt is too long' in lines[i]:
            doc_info['error'] = 'token_limit'
        else:
            doc_info['error'] = 'other'
        
        doc_info['error_msg'] = lines[i]
        failures.append(doc_info)
    i += 1

# Categorize and print
print(f"Total failures: {len(failures)}\n")

by_error = {}
for f in failures:
    error = f.get('error', 'unknown')
    if error not in by_error:
        by_error[error] = []
    by_error[error].append(f)

for error_type, docs in sorted(by_error.items()):
    print(f"\n{error_type.upper()}: {len(docs)} documents")
    print("=" * 80)
    for doc in docs:
        title = doc.get('title', 'Unknown')[:70]
        cf = doc.get('file', 'Unknown')
        bytes_val = doc.get('bytes', '?')
        print(f"  {title:70} | CF: {cf:15} | {bytes_val:>12} bytes")
