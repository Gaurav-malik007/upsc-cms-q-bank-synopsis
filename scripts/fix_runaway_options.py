import json
import re
import os

def fix_runaway_json(data):
    new_data = []
    changes_count = 0
    
    assertion_reason_v1 = "Both A and R are individually true and R is the correct explanation of A"
    assertion_reason_v2 = "Both A and R are individually true and R is NOT the correct explanation of A"
    
    for item in data:
        is_modified = False
        
        # Check all options
        for opt_key in ['a', 'b', 'c', 'd']:
            text = item['options'].get(opt_key, "")
            
            # Skip valid Assertion-Reasoning options
            if text.strip().lower().startswith("both a and r"):
                continue
                
            # Case 1: Explanation is inside an option
            if text.lower().startswith("explanation:"):
                exp_content = text[len("explanation:"):].strip()
                if not item.get('explanation'):
                    item['explanation'] = exp_content
                else:
                    item['explanation'] += " " + exp_content
                item['options'][opt_key] = "[Option cleaned - see explanation]"
                is_modified = True
                continue

            # Case 2: Runaway question (contains question numbers or obvious markers)
            if len(text) > 100:
                # Add more delimiters that often signal the start of a runaway section
                match = re.search(r'Answer:|Tip:|Explanation:|\bQ\d+\b|\d+\.|Select|EXCEPT|incorrect|Hallmark', text)
                if match and match.start() > 10: # ensure we don't truncate valid small starts
                    # Truncate at the first obvious break
                    item['options'][opt_key] = text[:match.start()].strip()
                    is_modified = True
                elif "(" in text and ")" in text and len(re.findall(r'\([a-d]\)', text)) > 1:
                    # Multiple option markers like (a) (b) inside an option
                    first_paren = text.find("(", 5) # skip the first paren if it was the start
                    if first_paren > 0:
                        item['options'][opt_key] = text[:first_paren].strip()
                        is_modified = True

        if is_modified:
            changes_count += 1
            print(f"Fixed {item['id']}")
            
        new_data.append(item)
        
    return new_data, changes_count

def main():
    path = r"c:\Users\deepa\Desktop\cms\public\data.js"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Find the start of the array [
        start = content.find("[")
        # Find the end of the array ]
        end = content.rfind("]") + 1
        if start == -1 or end == 0:
            print("Could not find JSON array in data.js")
            return
        json_str = content[start:end]
        data = json.loads(json_str)
    
    cleaned_data, fixed = fix_runaway_json(data)
    print(f"Identified {fixed} runaway entries.")
    
    # Write back
    with open(path, 'w', encoding='utf-8') as f:
        f.write("const mcqData = ")
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        f.write(";")

if __name__ == "__main__":
    main()
