import json
import os
import re

def merge_data():
    base_dir = r"c:\Users\deepa\Desktop\cms"
    data_js_file = os.path.join(base_dir, "public", "data.js")
    extracted_files = [
        (os.path.join(base_dir, "upsc_2020_extracted.json"), "2020"),
        (os.path.join(base_dir, "upsc_2021_extracted.json"), "2021")
    ]
    
    if not os.path.exists(data_js_file):
        print(f"Error: {data_js_file} not found.")
        return

    # Load all new data
    new_questions = []
    for file_path, year in extracted_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded {len(data)} questions for {year}.")
                new_questions.extend(data)
        else:
            print(f"Warning: {file_path} not found.")

    # Load existing data.js
    with open(data_js_file, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'const mcqData = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find mcqData array in data.js")
        return

    try:
        existing_data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    print(f"Loaded {len(existing_data)} existing questions.")

    # Filter out 2020 and 2021
    years_to_remove = ["2020", "2021"]
    filtered_data = [q for q in existing_data if q.get('year') not in years_to_remove]
    print(f"Removed existing {years_to_remove}. Remaining: {len(filtered_data)}")

    # Combine: New data first
    merged_data = new_questions + filtered_data
    print(f"Merged successfully. Total: {len(merged_data)}")

    # Save
    new_json = json.dumps(merged_data, indent=2)
    with open(data_js_file, 'w', encoding='utf-8') as f:
        f.write(f"const mcqData = {new_json};\n")
    
    print(f"Successfully updated {data_js_file}")

if __name__ == "__main__":
    merge_data()
