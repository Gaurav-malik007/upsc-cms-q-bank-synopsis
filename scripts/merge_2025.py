import json
import os
import re

def merge_data():
    extracted_file = r"c:\Users\deepa\Desktop\cms\upsc_2025_extracted.json"
    data_js_file = r"c:\Users\deepa\Desktop\cms\public\data.js"
    
    if not os.path.exists(extracted_file):
        print(f"Error: {extracted_file} not found.")
        return
    
    if not os.path.exists(data_js_file):
        print(f"Error: {data_js_file} not found.")
        return

    # Load new 2025 data
    with open(extracted_file, 'r', encoding='utf-8') as f:
        new_2025_data = json.load(f)
    print(f"Loaded {len(new_2025_data)} new 2025 questions.")

    # Load existing data.js
    with open(data_js_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the JSON array part
    # Pattern: const mcqData = [ ... ];
    match = re.search(r'const mcqData = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find mcqData array in data.js")
        return

    json_str = match.group(1)
    try:
        existing_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from data.js: {e}")
        # Try to pinpoint the error
        snippet = json_str[max(0, e.pos-50):min(len(json_str), e.pos+50)]
        print(f"Error near: ...{snippet}...")
        return

    print(f"Loaded {len(existing_data)} existing questions.")

    # Filter out existing 2025 entries
    filtered_data = [q for q in existing_data if q.get('year') != '2025']
    print(f"Removed existing 2025 questions. Remaining: {len(filtered_data)}")

    # Combine: New 2025 data at the TOP
    merged_data = new_2025_data + filtered_data
    print(f"Merged successfully. Total questions: {len(merged_data)}")

    # Save back to data.js
    # We want pretty-printed JSON inside the JS variable
    new_json_str = json.dumps(merged_data, indent=2)
    new_content = f"const mcqData = {new_json_str};\n"

    with open(data_js_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Successfully updated {data_js_file}")

if __name__ == "__main__":
    merge_data()
