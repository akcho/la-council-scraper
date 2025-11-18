import json
from pathlib import Path

# Council file 25-1037
cf_file = Path("data/councilfiles/25-1037.json")
with open(cf_file) as f:
    cf_data = json.load(f)

# Find the Appeal Response document
for att in cf_data.get('attachments', []):
    if 'Appeal Response' in att.get('text', ''):
        history_id = att.get('historyId')
        print(f"Found Appeal Response document:")
        print(f"  History ID: {history_id}")
        print(f"  Title: {att.get('text')}")
        
        # Load the summary
        summary_file = Path(f"data/pdf_summaries/{history_id}.json")
        if summary_file.exists():
            with open(summary_file) as f:
                summary_data = json.load(f)
            
            print("\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print(summary_data.get('summary', 'No summary found'))
            print("\n" + "=" * 80)
        else:
            print("\n❌ No summary file found")
        
        break
