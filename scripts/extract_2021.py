import fitz
import json
import re
import os

def clean_text(text):
    garbage = [
        r'For More High-Yield Medical',
        r'Notes & Updates',
        r'Follow & DM: @itsgauravmalikk',
        r'UPSC CMS 2021 \| PAPER \d',
        r'--- PAGE_BREAK ---'
    ]
    for pattern in garbage:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = text.replace(r' $\rightarrow$ ', ' -> ').replace(r'\rightarrow', '->').replace('$', '')
    return text.strip()

def extract_from_pdf(pdf_path, year, paper_num):
    if not os.path.exists(pdf_path): return []
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        words = page.get_text("words")
        words.sort(key=lambda w: (w[1] // 5, w[0]))
        full_text += " ".join([w[4] for w in words]) + "\n"
    doc.close()
    full_text = clean_text(full_text)
    q_blocks = re.split(r'([Qq]\s*\d+\.)', full_text)
    questions = []
    for i in range(1, len(q_blocks), 2):
        q_label, q_content = q_blocks[i], q_blocks[i+1]
        q_num_match = re.search(r'(\d+)', q_label)
        if not q_num_match: continue
        q_num_str = q_num_match.group(1)
        q_num = int(q_num_str)
        ans_match = list(re.finditer(r'Answer:\s*\(([a-d])\)', q_content, re.IGNORECASE))
        if not ans_match: ans_match = list(re.finditer(r'(?:Answer|Ans):\s*\(?([a-d])\)?', q_content, re.IGNORECASE))
        if ans_match:
            last_ans = ans_match[-1]
            pre_ans, post_ans, answer = q_content[:last_ans.start()], q_content[last_ans.start():], last_ans.group(1).lower()
        else:
            pre_ans, post_ans, answer = q_content, "", ""
        exp_match = re.search(r'(?:Tip:|Explanation:|>\s*Tip:|Ans:)[\s]*\)?\s*(.*)', post_ans, re.DOTALL | re.IGNORECASE)
        if not exp_match and post_ans: exp_match = re.search(r'(?:Answer|Ans):\s*\(?[a-d]\)?\s*(.*)', post_ans, re.DOTALL | re.IGNORECASE)
        explanation = clean_text(re.sub(r'\s+', ' ', exp_match.group(1)).strip()) if exp_match else ""
        opt_indices = sorted([(m.start(), m.end(), char) for char in ['a', 'b', 'c', 'd'] for m in [re.search(rf'\({char}\)', pre_ans, re.IGNORECASE)] if m])
        options = {}
        if opt_indices:
            question_text = clean_text(pre_ans[:opt_indices[0][0]])
            for idx in range(len(opt_indices)):
                start, end = opt_indices[idx][1], opt_indices[idx+1][0] if idx+1 < len(opt_indices) else len(pre_ans)
                options[opt_indices[idx][2].lower()] = clean_text(re.sub(r'\s+', ' ', pre_ans[start:end]).strip())
        else:
            question_text = clean_text(pre_ans)
        
        # Subject mapping
        if paper_num == "1": subject = "Medicine" if q_num <= 96 else "Pediatrics"
        else:
            if q_num <= 40: subject = "Surgery"
            elif q_num <= 80: subject = "Obstetrics & Gynecology"
            else: subject = "PSM"
            
        questions.append({"id": f"UPSC_{year}_P{paper_num}_Q{q_num_str}", "num": q_num_str, "question": question_text, "options": options, "answer": answer, "explanation": explanation, "year": year, "paper": paper_num, "tags": [subject]})
    return questions

def main():
    base = r"c:\Users\deepa\Desktop\cms\new pdf"
    papers = [(os.path.join(base, "new UPSC CMS 2021 PAPER 1.pdf"), "2021", "1"), (os.path.join(base, "new UPSC CMS 2021 PAPER 2.pdf"), "2021", "2")]
    all_qs = []
    for pdf, yr, num in papers:
        qs = extract_from_pdf(pdf, yr, num)
        print(f"Paper {num}: {len(qs)} questions.")
        all_qs.extend(qs)
    with open(r"c:\Users\deepa\Desktop\cms\upsc_2021_extracted.json", 'w', encoding='utf-8') as f: json.dump(all_qs, f, indent=2, ensure_ascii=False)
if __name__ == "__main__": main()
