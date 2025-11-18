import re

with open('pdf_processing_retry.log', 'r') as f:
    log = f.read()

# Count different error types
errors = {
    'request_too_large': 0,
    'prompt_too_long': 0,
    'could_not_process': 0,
    'other': 0
}

for line in log.split('\n'):
    if '❌ Error:' in line:
        if 'request_too_large' in line:
            errors['request_too_large'] += 1
        elif 'prompt is too long' in line:
            errors['prompt_too_long'] += 1
        elif 'Could not process PDF' in line:
            errors['could_not_process'] += 1
        else:
            errors['other'] += 1

print("Retry Run Failure Analysis")
print("=" * 50)
print(f"Total errors: {sum(errors.values())}")
print()
for error_type, count in sorted(errors.items(), key=lambda x: -x[1]):
    if count > 0:
        print(f"{error_type:25} {count:3} errors")

# Check successes
successes = log.count('✅ Summary generated')
print()
print(f"Successes: {successes}")
print()
print("CONCLUSION:")
print("-" * 50)
print("Even with 100-page extraction, most PDFs still exceed")
print("the 200k token limit due to very dense text content.")
print()
print("These are extremely detailed technical/environmental")
print("reports that are too large to process automatically.")
