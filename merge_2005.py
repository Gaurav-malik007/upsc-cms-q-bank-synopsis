import json
import os

def merge_2005():
    # 1. Load existing data.js
    data_js_path = 'data.js'
    if os.path.exists(data_js_path):
        with open(data_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
            json_str = content.split('=', 1)[1].strip().rstrip(';')
            all_data = json.loads(json_str)
    else:
        all_data = []
    
    # 2. Load 2005 extraction
    with open('upsc_2005_p1.json', 'r', encoding='utf-8') as f:
        data_2005 = json.load(f)
    
    # 3. Deduplicate Q99 and internal duplicates
    seen_ids = set()
    cleaned_2005 = []
    for q in data_2005:
        if q['id'] not in seen_ids:
            cleaned_2005.append(q)
            seen_ids.add(q['id'])
    
    # 4. Remove any existing 2005 questions from all_data (to replaced with high-yield)
    # Though we cleared 2005-2019, let's be safe.
    merged = [q for q in all_data if q['year'] != '2005']
    merged.extend(cleaned_2005)
    
    # 5. Sort by year (desc), then paper, then num (numerical)
    merged.sort(key=lambda x: (int(x['year']), int(x['paper']), int(re.sub(r'\D', '', x['num']))), reverse=True)
    
    # 6. Write back to data.js
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write("const mcqData = ")
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write(";")
    
    print(f"Merged {len(cleaned_2005)} questions from 2005. Total questions: {len(merged)}")

import re
if __name__ == "__main__":
    merge_2005()
