import fitz
import json
import re
import os

def extract_from_pdf(pdf_path, year, paper):
    print(f"Extracting from {pdf_path} ({year} P{paper})...")
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    
    full_text = full_text.replace('\r\n', '\n')
    
    # Improved pattern: Handles Q1. at start of line OR after a space/tag
    q_blocks = re.split(r'(?:\n|\s|^|\])(Q\d+\.)', full_text)
    
    questions = []
    
    for i in range(1, len(q_blocks), 2):
        q_label = q_blocks[i]
        q_content = q_blocks[i+1]
        q_num = re.search(r'\d+', q_label).group()
        
        # Extract Answer - handles (a) or just a
        ans_match = re.search(r'Answer:\s*(?:\()?\s*([a-d])(?:\))?', q_content, re.I)
        if not ans_match:
            continue
            
        answer = ans_match.group(1).lower()
        
        # Extract Explanation if exists
        exp_match = re.search(r'(?:Explanation:|\| Tip:|\| Explanation:|Tip:)\s*(.*)', q_content, re.DOTALL)
        explanation = exp_match.group(1).strip() if exp_match else ""
        # Cut explanation at next header or tag if necessary
        explanation = re.split(r'\[Subject:', explanation)[0].strip()
        explanation = explanation.replace('\n', '<br>')
        
        # Options
        opt_matches = re.findall(r'\(([a-d])\)\s*([^()]*?)(?=\s*\([a-d]\)|\s*Answer:|\s*Code:|$)', q_content, re.I | re.DOTALL)
        options = {}
        for char, val in opt_matches:
            options[char.lower()] = val.strip().replace('\n', ' ')
        
        # Question text - usually from start of content to first option (a)
        if '(a)' in q_content:
            q_text = q_content.split('(a)')[0].strip().replace('\n', ' ')
        else:
            q_text = q_content.split('Answer:')[0].strip().replace('\n', ' ')
        
        # Clean question text from trailing trash
        q_text = re.split(r'\[Subject:', q_text)[0].strip()

        # Subject mapping
        subject = "General"
        try:
            ni = int(q_num)
            if paper == "1":
                subject = "Medicine" if ni <= 80 else "Pediatrics"
            elif paper == "2":
                if ni <= 40: subject = "Surgery"
                elif ni <= 80: subject = "OBGYN"
                else: subject = "PSM"
        except:
            pass

        questions.append({
            "id": f"UPSC_{year}_P{paper}_Q{q_num}",
            "num": q_num,
            "question": q_text,
            "options": options,
            "answer": answer,
            "explanation": explanation,
            "year": str(year),
            "paper": str(paper),
            "tags": [subject]
        })
    
    print(f"Found {len(questions)} valid questions.")
    return questions

def run_extraction():
    all_new_questions = []
    pdf_dir = "pyq pdf"
    
    files = os.listdir(pdf_dir)
    for filename in files:
        if not filename.lower().endswith('.pdf'): continue
        
        # Auto-detect year and paper from filename
        year_match = re.search(r'20\d{2}', filename)
        paper_match = re.search(r'paper\s*([12])', filename, re.I)
        
        if year_match and paper_match:
            year = year_match.group()
            paper = paper_match.group(1)
            path = os.path.join(pdf_dir, filename)
            qs = extract_from_pdf(path, year, paper)
            all_new_questions.extend(qs)

    # Also handle the 2005 files in the root if they are not already there
    root_p1 = 'UPSC CMS 2005 PAPER 1.pdf'
    root_p2 = 'UPSC CMS 2005 PAPER 2.pdf'
    if os.path.exists(root_p1): all_new_questions.extend(extract_from_pdf(root_p1, '2005', '1'))
    if os.path.exists(root_p2): all_new_questions.extend(extract_from_pdf(root_p2, '2005', '2'))

    with open("new_extracted_data.json", "w", encoding="utf-8") as f:
        json.dump(all_new_questions, f, indent=2, ensure_ascii=False)
    print(f"Total extracted: {len(all_new_questions)}")

if __name__ == "__main__":
    run_extraction()
