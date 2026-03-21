import json
import os
import re

def merge_data():
    extracted_file = r"c:\Users\deepa\Desktop\cms\upsc_2023_extracted.json"
    data_js_file = r"c:\Users\deepa\Desktop\cms\public\data.js"
    
    if not os.path.exists(extracted_file):
        print(f"Error: {extracted_file} not found.")
        return
    
    if not os.path.exists(data_js_file):
        print(f"Error: {data_js_file} not found.")
        return

    with open(extracted_file, 'r', encoding='utf-8') as f:
        new_2023_data = json.load(f)
    print(f"Loaded {len(new_2023_data)} new 2023 questions.")

    with open(data_js_file, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'const mcqData = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find mcqData array in data.js")
        return

    json_str = match.group(1)
    try:
        existing_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from data.js: {e}")
        return

    print(f"Loaded {len(existing_data)} existing questions.")

    # Filter out existing 2023 entries
    filtered_data = [q for q in existing_data if str(q.get('year')) != '2023']
    print(f"Removed existing 2023 questions. Remaining: {len(filtered_data)}")

    # Put 2025, 2024, then 2023, then others (chronological descending)
    p2025 = [q for q in filtered_data if str(q.get('year')) == '2025']
    p2024 = [q for q in filtered_data if str(q.get('year')) == '2024']
    others = [q for q in filtered_data if str(q.get('year')) not in ('2025','2024')]
    
    merged_data = p2025 + p2024 + new_2023_data + others
    print(f"Merged successfully. Total questions: {len(merged_data)}")

    new_json_str = json.dumps(merged_data, indent=2)
    new_content = f"const mcqData = {new_json_str};\n"

    with open(data_js_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Successfully updated {data_js_file}")

if __name__ == "__main__":
    merge_data()
