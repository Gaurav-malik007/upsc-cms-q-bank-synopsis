import json
import os
import re

def merge_2005_p2():
    data_js_path = 'data.js'
    if os.path.exists(data_js_path):
        with open(data_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
            json_str = content.split('=', 1)[1].strip().rstrip(';')
            all_data = json.loads(json_str)
    else:
        all_data = []
    
    with open('upsc_2005_p2.json', 'r', encoding='utf-8') as f:
        data_2005_p2 = json.load(f)
    
    # Deduplicate internally if any
    seen_ids = set()
    cleaned_2005_p2 = []
    for q in data_2005_p2:
        if q['id'] not in seen_ids:
            cleaned_2005_p2.append(q)
            seen_ids.add(q['id'])
    
    # Replace existing 2005 P2 questions if any
    merged = [q for q in all_data if not (q['year'] == '2005' and q['paper'] == '2')]
    merged.extend(cleaned_2005_p2)
    
    # Sort
    merged.sort(key=lambda x: (int(x['year']), int(x['paper']), int(re.sub(r'\D', '', x['num']))), reverse=True)
    
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write("const mcqData = ")
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write(";")
    
    print(f"Merged {len(cleaned_2005_p2)} questions from 2005 P2. Total questions: {len(merged)}")

if __name__ == "__main__":
    merge_2005_p2()
