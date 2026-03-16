import fitz
import json
import re

def parse_table_to_html(text):
    lines = [line.strip() for line in text.split('\n')]
    table_lines = [line for line in lines if '|' in line]
    if not table_lines: return text.replace('\n', '<br>')
    
    html = '<div class="table-container"><table class="explanation-table">'
    has_content = False
    for line in table_lines:
        cols = [c.strip() for c in line.split('|')]
        if cols and not cols[0]: cols = cols[1:]
        if cols and not cols[-1]: cols = cols[:-1]
        if not cols or all(c == ':' or c == '-' or set(c) == {'-', ':'} for c in cols): continue
        html += '<tr>'
        for col in cols: html += f'<td>{col}</td>'
        html += '</tr>'
        has_content = True
    html += '</table></div>'
    
    if not has_content: return text.replace('\n', '<br>')
    
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

def extract_2005_p2(pdf_path, output_json):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc: full_text += page.get_text()
    full_text = full_text.replace('\r\n', '\n')
    
    # Split by Q[Number].
    q_blocks = re.split(r'(Q\d+\.)', full_text)
    
    questions = []
    
    # q_blocks[0] is header
    # q_blocks[i] is Qx., q_blocks[i+1] is content
    for i in range(1, len(q_blocks), 2):
        q_label = q_blocks[i]
        q_content = q_blocks[i+1]
        q_num = q_label.strip('Q. ')
        
        # Subject extraction from [Subject: ...]
        subj_match = re.search(r'\[Subject:\s*(.*?)(?:\||\])', q_content, re.I)
        raw_subject = subj_match.group(1).strip() if subj_match else "Surgery"
        
        # Mapping to primary subjects
        subject = "Surgery"
        if "OBGYN" in raw_subject.upper(): subject = "OBGYN"
        elif "PSM" in raw_subject.upper(): subject = "PSM"
        elif "PEDIATRICS" in raw_subject.upper(): subject = "Pediatrics" # Keep if explicit
        elif "MEDICINE" in raw_subject.upper(): subject = "Medicine"
        
        # 1. Answer
        # Paper 2 format: Answer: c (1, 3, and 4)
        ans_match = re.search(r'Answer:\s*([a-d])\b', q_content, re.I)
        if not ans_match: continue
        answer = ans_match.group(1).lower()
        
        # 2. Explanation
        # In this PDF, explanation often comes after Answer: x (...)
        exp_match = re.search(r'Answer:\s*[a-d]\s*\(.*?\)\s*(Explanation:.*|\| Tip:.*)', q_content, re.DOTALL | re.I)
        explanation = ""
        if exp_match:
            explanation = exp_match.group(1).strip()
        else:
            # Try finding Explanation: directly
            exp_match = re.search(r'(?:Explanation:|\| Tip:)\s*(.*)', q_content, re.DOTALL | re.I)
            explanation = exp_match.group(1).strip() if exp_match else ""
            
        if '|' in explanation:
            explanation = parse_table_to_html(explanation)
        else:
            explanation = explanation.replace('\n', '<br>')
            
        # 3. Question Text
        # Question text is between the subject bracket and (a)
        # OR just after Qx.
        q_text = q_content.split('(a)')[0].strip().replace('\n', ' ')
        if ']' in q_text:
            q_text = q_text.split(']')[-1].strip()

        # 4. Options
        all_opts = re.findall(r'\(([a-d])\)\s*([^()]*?)(?=\s*\([a-d]\)|\s*Answer:|$)', q_content, re.I | re.DOTALL)
        options = {}
        if len(all_opts) >= 4:
            for char, val in all_opts[:4]:
                options[char.lower()] = val.strip().replace('\n', ' ')
        
        questions.append({
            "id": f"UPSC_2005_P2_Q{q_num}",
            "num": q_num,
            "question": q_text,
            "options": options,
            "answer": answer,
            "explanation": explanation,
            "year": "2005",
            "paper": "2",
            "tags": [subject]
        })

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(questions)} questions to {output_json}")

if __name__ == "__main__":
    extract_2005_p2('UPSC CMS 2005 PAPER 2.pdf', 'upsc_2005_p2.json')
