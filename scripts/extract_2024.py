import fitz
import json
import re
import os

def clean_text(text):
    # Remove obvious headers/footers/promotions
    garbage = [
        r'For More High-Yield Medical',
        r'Notes & Updates',
        r'Follow & DM: @itsgauravmalikk?',
        r'UPSC CMS 2024 \| PAPER \d',
        r'UPSC CMS 2025 \| PAPER \d',
        r'PART \d+:.*?\n',
        r'--- PAGE_BREAK ---'
    ]
    for pattern in garbage:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove stand-alone page numbers on a line
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # Character cleanup
    text = text.replace(r' $\rightarrow$ ', ' -> ')
    text = text.replace(r'\rightarrow', '->')
    text = text.replace('$', '')
    
    return text.strip()

def extract_from_pdf(pdf_path, year, paper_num):
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return []

    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        blocks = page.get_text("blocks")
        # Column-aware sorting: left column first, then right column
        blocks.sort(key=lambda b: (b[0] > (page.rect.width/2), b[1]))
        for b in blocks:
            full_text += b[4] + "\n"
    doc.close()

    full_text = clean_text(full_text)
    
    # Split by Qnn. prefix
    q_blocks = re.split(r'\n\s*(Q\d+\.)', "\n" + full_text)
    
    questions = []
    
    for i in range(1, len(q_blocks), 2):
        q_label = q_blocks[i]
        q_content = q_blocks[i+1]
        
        q_num_match = re.search(r'(\d+)', q_label)
        if not q_num_match: continue
        q_num_str = q_num_match.group(1)
        q_num = int(q_num_str)
        
        # Split Answer:
        ans_split = re.split(r'\n\s*Answer:', q_content, flags=re.IGNORECASE)
        if len(ans_split) < 2:
            ans_split = re.split(r'Answer:', q_content, flags=re.IGNORECASE)
            
        if len(ans_split) < 2:
            ans_match = re.search(r'Answer:\s*\(([a-d])\)', q_content, re.IGNORECASE)
            if not ans_match: continue
            pre_ans = q_content[:ans_match.start()]
            post_ans = q_content[ans_match.start():]
        else:
            pre_ans = ans_split[0]
            post_ans = "Answer:" + "Answer:".join(ans_split[1:])
        
        # Extract Answer
        ans_letter_match = re.search(r'Answer:\s*\(([a-d])\)', post_ans, re.IGNORECASE)
        answer = ans_letter_match.group(1).lower() if ans_letter_match else ""
        
        # Extract Explanation
        exp_match = re.search(r'(?:Tip:|Explanation:|>\s*Tip:|Ans:)[\s]*\)?\s*(.*)', post_ans, re.DOTALL | re.IGNORECASE)
        if not exp_match:
            exp_match = re.search(r'Answer:\s*\([a-d]\)\s*(.*)', post_ans, re.DOTALL | re.IGNORECASE)

        explanation = exp_match.group(1).strip() if exp_match else ""
        explanation = re.sub(r'\s+', ' ', explanation).strip()
        explanation = clean_text(explanation)
        
        # Extract Options
        opt_indices = []
        for char in ['a', 'b', 'c', 'd']:
            m = re.search(rf'\({char}\)', pre_ans, re.IGNORECASE)
            if m:
                opt_indices.append((m.start(), m.end(), char))
        
        opt_indices.sort()
        
        options = {}
        if opt_indices:
            question_text = pre_ans[:opt_indices[0][0]].strip()
            for idx in range(len(opt_indices)):
                start_content = opt_indices[idx][1]
                end_content = opt_indices[idx+1][0] if idx+1 < len(opt_indices) else len(pre_ans)
                opt_char = opt_indices[idx][2].lower()
                opt_val = pre_ans[start_content:end_content].strip()
                opt_val = re.sub(r'\s+', ' ', opt_val).strip()
                options[opt_char] = clean_text(opt_val)
        else:
            question_text = pre_ans.strip()

        question_text = re.sub(r'\s+', ' ', question_text).strip()
        question_text = clean_text(question_text).strip()
        
        # 2024 Subject Mapping
        subject = "Unknown"
        if paper_num == "1":
            subject = "Medicine" if q_num <= 96 else "Pediatrics"
        else:
            if q_num <= 40: subject = "Surgery"
            elif q_num <= 80: subject = "Obstetrics & Gynecology"
            else: subject = "PSM"
            
        questions.append({
            "id": f"UPSC_{year}_P{paper_num}_Q{q_num_str}",
            "num": q_num_str,
            "question": question_text,
            "options": options,
            "answer": answer,
            "explanation": explanation,
            "year": year,
            "paper": paper_num,
            "tags": [subject]
        })
        
    return questions

def main():
    base_dir = r"c:\Users\deepa\Desktop\cms"
    papers = [
        (os.path.join(base_dir, "new pdf", "new upsc cms 2024 paper 1.pdf"), "2024", "1"),
        (os.path.join(base_dir, "new pdf", "new UPSC CMS 2024 PAPER 2.pdf"), "2024", "2")
    ]
    
    all_extracted = []
    for pdf, year, num in papers:
        print(f"Extracting {pdf}...")
        qs = extract_from_pdf(pdf, year, num)
        print(f"  Extracted {len(qs)} questions.")
        all_extracted.extend(qs)
        
    output_file = os.path.join(base_dir, "upsc_2024_extracted.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_extracted, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved total {len(all_extracted)} questions to {output_file}")

if __name__ == "__main__":
    main()
