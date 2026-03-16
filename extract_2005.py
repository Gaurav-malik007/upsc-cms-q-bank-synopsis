import fitz
import json
import re

def parse_table_to_html(text):
    # Detect pipe-separated lines
    lines = [line.strip() for line in text.split('\n')]
    table_lines = [line for line in lines if '|' in line]
    
    if not table_lines:
        return text.replace('\n', '<br>')
    
    # Simple table reconstruction
    html = '<div class="table-container"><table class="explanation-table">'
    has_content = False
    for line in table_lines:
        # Split and clean columns
        cols = [c.strip() for c in line.split('|')]
        # Filter out empty leading/trailing cells
        if cols and not cols[0]: cols = cols[1:]
        if cols and not cols[-1]: cols = cols[:-1]
        
        if not cols or all(c == ':' or c == '-' or set(c) == {'-', ':'} for c in cols): 
            continue # Skip header separator lines
            
        html += '<tr>'
        for col in cols:
            html += f'<td>{col}</td>'
        html += '</tr>'
        has_content = True
        
    html += '</table></div>'
    
    if not has_content:
        return text.replace('\n', '<br>')
    
    # Text before/after table
    pre_text = []
    for line in lines:
        if '|' not in line: pre_text.append(line)
        else: break
        
    post_text = []
    for line in reversed(lines):
        if '|' not in line: post_text.append(line)
        else: break
    post_text.reverse()
    
    final_parts = []
    if pre_text: final_parts.append('<br>'.join(pre_text))
    final_parts.append(html)
    if post_text: final_parts.append('<br>'.join(post_text))
    
    return '<br>'.join(final_parts)

def extract_2005(pdf_path, output_json):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    
    full_text = full_text.replace('\r\n', '\n')
    
    # The PDF has a "compilation" section at the end which repeats some questions.
    # Let's split by Q[Number].
    q_blocks = re.split(r'\n(Q\d+\.)', full_text)
    
    questions_dict = {} # Keyed by num to handle duplicates/overwrites
    
    for i in range(1, len(q_blocks), 2):
        q_label = q_blocks[i]
        q_content = q_blocks[i+1]
        q_num = q_label.strip('Q. ')
        
        # 1. Extract Answer
        ans_match = re.search(r'Answer:\s*\(([a-d])\)', q_content, re.I)
        if not ans_match:
            # Look for cases like "Answer: (b) 3 only"
            ans_match = re.search(r'Answer:\s*\(([a-d])\)', q_content, re.I)
            if not ans_match: continue
            
        answer = ans_match.group(1).lower()
        
        # 2. Extract Explanation
        exp_match = re.search(r'(?:Explanation:|\| Tip:)\s*(.*)', q_content, re.DOTALL)
        explanation = exp_match.group(1).strip() if exp_match else ""
        if '|' in explanation:
            explanation = parse_table_to_html(explanation)
        else:
            explanation = explanation.replace('\n', '<br>')
        
        # 3. Question Text
        if 'Match list' in q_content:
            q_text_parts = re.split(r'(List I|List II)', q_content)
            q_base = q_text_parts[0].strip()
            # Try to format the lists
            lists_text = ""
            if len(q_text_parts) > 1:
                lists_text = "<br><br>" + "".join(q_text_parts[1:]).split('Code:')[0].strip()
                lists_text = lists_text.replace('\n', '<br>')
            q_text = f"<strong>{q_base}</strong>{lists_text}"
        else:
            # Handle split questions like Q100
            q_text = q_content.split('(a)')[0].strip().replace('\n', ' ')
            
        # 4. Options
        all_opts = re.findall(r'\(([a-d])\)\s*([^()]*?)(?=\s*\([a-d]\)|\s*Answer:|\s*Code:|$)', q_content, re.I | re.DOTALL)
        options = {}
        if len(all_opts) >= 4:
            for char, val in all_opts[:4]:
                options[char.lower()] = val.strip().replace('\n', ' ')
        elif 'Code:' in q_content:
            # Try code-style options
            code_opts = re.findall(r'\(([a-d])\)\s*([^()]*?)(?=\s*\([a-d]\)|\s*Answer:|$)', q_content.split('Code:')[1], re.I | re.DOTALL)
            for char, val in code_opts[:4]:
                options[char.lower()] = val.strip().replace('\n', ' ')
        
        num_int = int(q_num)
        subject = "Medicine"
        if num_int > 80: subject = "Pediatrics"
            
        # Store or Update (later versions usually have better tips/formatting)
        # But if the current one has a table, it's probably better.
        if q_num not in questions_dict or '|' in q_content:
            questions_dict[q_num] = {
                "id": f"UPSC_2005_P1_Q{q_num}",
                "num": q_num,
                "question": q_text,
                "options": options,
                "answer": answer,
                "explanation": explanation,
                "year": "2005",
                "paper": "1",
                "tags": [subject]
            }

    # Convert dict to sorted list
    final_questions = [questions_dict[str(n)] for n in range(1, 121) if str(n) in questions_dict]

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_questions, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(final_questions)} questions to {output_json}")

if __name__ == "__main__":
    extract_2005('UPSC CMS 2005 PAPER 1.pdf', 'upsc_2005_p1.json')
