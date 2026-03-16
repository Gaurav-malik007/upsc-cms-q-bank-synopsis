import json

def update_data_js(json_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Sort for consistency: Year desc, Paper asc, Num asc
    data.sort(key=lambda x: (x['year'], x['paper'], int(x['num'])), reverse=True)
    
    # But reverse only year, keep paper/num asc
    data.sort(key=lambda x: (-int(x['year']), int(x['paper']), int(x['num'])))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("const mcqData = ")
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write(";")
    
    print(f"Updated {output_path} with {len(data)} questions.")

if __name__ == "__main__":
    update_data_js("new_extracted_data.json", "data.js")
