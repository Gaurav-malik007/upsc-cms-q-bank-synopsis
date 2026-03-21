import fitz
import json
import re
import os

def clean_text(text):
    # Remove obvious headers/footers/promotions
    garbage = [
        r'For More High-Yield Medical',
        r'Notes & Updates',
        r'Follow & DM: @itsgauravmalikk',
        r'UPSC CMS 2022 \| PAPER \d',
        r'--- PAGE_BREAK ---'
    ]
    for pattern in garbage:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove stand-alone page numbers on a line
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # Character cleanup for LaTeX style arrows
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
        # USE WORDS for robust reconstruction
        words = page.get_text("words")
        # Sort by y (with 5pt tolerance) then x
        words.sort(key=lambda w: (w[1] // 5, w[0]))
        page_text = " ".join([w[4] for w in words])
        full_text += page_text + "\n"
    doc.close()

    full_text = clean_text(full_text)
    
    # Split by Q followed by number (allow space: Q 1.)
    q_blocks = re.split(r'([Qq]\s*\d+\.)', full_text)
    
    questions = []
    
    # q_blocks[0] is header/intro
    for i in range(1, len(q_blocks), 2):
        q_label = q_blocks[i]
        q_content = q_blocks[i+1]
        
        q_num_match = re.search(r'(\d+)', q_label)
        if not q_num_match: continue
        q_num_str = q_num_match.group(1)
        q_num = int(q_num_str)
        
        # 1. Find the Answer line. Use the LAST occurrence of "Answer: (x)"
        ans_match = list(re.finditer(r'Answer:\s*\(([a-d])\)', q_content, re.IGNORECASE))
        if not ans_match:
            # Fallback for just "Answer: x" or "Ans: x"
            ans_match = list(re.finditer(r'(?:Answer|Ans):\s*\(?([a-d])\)?', q_content, re.IGNORECASE))
            
        if ans_match:
            last_ans = ans_match[-1]
            pre_ans = q_content[:last_ans.start()]
            post_ans = q_content[last_ans.start():]
            answer = last_ans.group(1).lower()
        else:
            pre_ans = q_content
            post_ans = ""
            answer = ""
        
        # 2. Extract Explanation / Tip from post_ans
        exp_match = re.search(r'(?:Tip:|Explanation:|>\s*Tip:|Ans:)[\s]*\)?\s*(.*)', post_ans, re.DOTALL | re.IGNORECASE)
        if not exp_match and post_ans:
            # Fallback: everything after "Answer: (x)"
            exp_match = re.search(r'(?:Answer|Ans):\s*\(?[a-d]\)?\s*(.*)', post_ans, re.DOTALL | re.IGNORECASE)

        explanation = exp_match.group(1).strip() if exp_match else ""
        explanation = re.sub(r'\s+', ' ', explanation).strip()
        explanation = clean_text(explanation)
        
        # 3. Extract Options from pre_ans
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
        (os.path.join(base_dir, "new pdf", "new UPSC CMS 2022 PAPER 1.pdf"), "2022", "1"),
        (os.path.join(base_dir, "new pdf", "new UPSC CMS 2022 PAPER 2.pdf"), "2022", "2")
    ]
    
    all_extracted = []
    for pdf, year, num in papers:
        print(f"Extracting {pdf}...")
        qs = extract_from_pdf(pdf, year, num)
        print(f"  Extracted {len(qs)} questions for Paper {num}.")
        all_extracted.extend(qs)
        
    output_file = os.path.join(base_dir, "upsc_2022_extracted.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_extracted, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved total {len(all_extracted)} questions to {output_file}")

if __name__ == "__main__":
    main()
