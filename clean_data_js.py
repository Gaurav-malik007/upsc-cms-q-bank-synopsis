import json
import re
import os

DATA_JS_PATH = 'data.js'
CLEANED_DATA_JS_PATH = 'data_cleaned.js'

def clean_data():
    if not os.path.exists(DATA_JS_PATH):
        print(f"Error: {DATA_JS_PATH} not found.")
        return

    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract JSON from data.js
    try:
        json_str = content.split('=', 1)[1].strip().rstrip(';')
        data = json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return

    cleaned_count = 0
    option_split_count = 0
    answer_fixed_count = 0

    option_pattern = re.compile(r'[\(\{\[]?([a-d])[\)\}\]\.]\s*(.+?)(?=\s*[\(\{\[]?[a-d][\)\}\]\.]|$)')

    for q in data:
        options = q.get('options', {})
        new_options = {}
        
        # 1. Split merged options
        items_to_process = list(options.items())
        combined_text = ""
        for key, text in items_to_process:
            # If the text itself contains (b), (c), (d) etc.
            matches = option_pattern.findall(text)
            if matches:
                for letter, opt_text in matches:
                    new_options[letter.lower()] = opt_text.strip()
            else:
                new_options[key.lower()] = text.strip()

        # If we found more options or fixed structure, update
        if new_options != options:
            q['options'] = new_options
            option_split_count += 1

        # 2. Check Answer Validity
        ans = q.get('answer', '').lower()
        if ans and ans not in q['options']:
            # Maybe the answer text is in the explanation?
            # Or hidden in another option's text?
            # Actually, most of the time it was just a splitting issue.
            # If still missing, we leave it for manual or later fix.
            answer_fixed_count += 1
        
        cleaned_count += 1

    # Save to data.js (overwrite)
    new_js_content = "const mcqData = " + json.dumps(data, indent=2) + ";"
    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(new_js_content)

    print(f"Total processed: {cleaned_count}")
    print(f"Questions with split options: {option_split_count}")
    print(f"Questions with invalid answers remaining: {answer_fixed_count}")

if __name__ == "__main__":
    clean_data()
