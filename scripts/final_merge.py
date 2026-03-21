import json
import os

def main():
    data_js_path = r"c:\Users\deepa\Desktop\cms\public\data.js"
    new_extracted_path = r"c:\Users\deepa\Desktop\cms\new_fully_extracted_data.json"
    
    # Load data.js
    with open(data_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
        start = content.find("[")
        end = content.rfind("]") + 1
        old_questions = json.loads(content[start:end])
        
    # Load new extracted data
    with open(new_extracted_path, 'r', encoding='utf-8') as f:
        new_extracted = json.load(f)
        
    # We want to keep 2005 from old_questions, 
    # but replace 2020-2025 with new_extracted
    final_questions = []
    
    # 1. Add 2005 from old questions
    for q in old_questions:
        if q['year'] == '2005':
            final_questions.append(q)
            
    # 2. Add all from new_extracted (covers 2020-2025)
    # We use a set to avoid duplicates by ID
    seen_ids = set(q['id'] for q in final_questions)
    for q in new_extracted:
        if q['id'] not in seen_ids:
            final_questions.append(q)
            seen_ids.add(q['id'])
            
    # Write back to data.js
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write("const mcqData = ")
        json.dump(final_questions, f, indent=2, ensure_ascii=False)
        f.write(";")
        
    print(f"Final merge complete. Total questions: {len(final_questions)}")

if __name__ == "__main__":
    main()
