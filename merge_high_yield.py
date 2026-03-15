import json
import os
import re

DATA_JS_PATH = 'data.js'
NEW_DATA_DIR = 'high_yield_extraction'

def merge_new_data():
    if not os.path.exists(DATA_JS_PATH):
        print(f"Error: {DATA_JS_PATH} not found.")
        return

    # 1. Load existing data
    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        json_str = content.split('=', 1)[1].strip().rstrip(';')
        data = json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    # 2. Filter out 2020-2025 questions from existing data
    # (We are replacing them with high-quality versions)
    data = [q for q in data if not (q.get('year') and int(q.get('year')) >= 2020)]
    print(f"Existing questions (2005-2019) kept: {len(data)}")

    # 3. Load new high-quality questions
    new_questions = []
    for filename in os.listdir(NEW_DATA_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(NEW_DATA_DIR, filename), 'r', encoding='utf-8') as f:
                new_questions.extend(json.load(f))
    
    print(f"New high-quality questions (2020-2025) added: {len(new_questions)}")

    # 4. Combine
    all_data = data + new_questions

    # 5. Save back to data.js
    new_js_content = "const mcqData = " + json.dumps(all_data, indent=2) + ";"
    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(new_js_content)
    
    print(f"Final data.js size: {len(all_data)} questions.")

if __name__ == "__main__":
    merge_new_data()
