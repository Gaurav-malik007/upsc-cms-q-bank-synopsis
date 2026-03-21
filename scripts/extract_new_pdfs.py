import fitz
import json
import re
import os
import sys

def parse_pdf(pdf_path, year, paper):
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return []
    
    print(f"Processing {pdf_path} (Year: {year}, Paper: {paper})...")
    doc = fitz.open(pdf_path)
    # Reconstruct text carefully by sorting words
    full_text = ""
    for page in doc:
        words = page.get_text("words")
        mid_x = page.rect.width / 2
        
        left_words = [w for w in words if w[0] < mid_x]
        right_words = [w for w in words if w[0] >= mid_x]
        
        page_text = ""
        for column_words in [left_words, right_words]:
            # Sort by y0 first, then x0
            column_words.sort(key=lambda w: (int(w[1] / 3), w[0]))
            
            current_y = -1
            for w in column_words:
                if current_y != -1 and abs(w[1] - current_y) > 3:
                    page_text += "\n"
                elif current_y != -1:
                    page_text += " "
                page_text += w[4]
                current_y = w[1]
            page_text += "\n\n"
        full_text += page_text + "\n"
    
    doc.close()

    
    # Normalize line endings and spaces
    full_text = full_text.replace('\r\n', '\n').replace('\r', '\n')
    # Remove excessive blank lines
    full_text = re.sub(r'\n\s*\n', '\n\n', full_text)
    
    # Split into question blocks
    # Looking for patterns like Q1. or 1. at the start of a line
    # Sometimes it's Q.1 or Q 1.
    # The new PDFs seem to use Q1., Q2., etc.
    q_blocks = re.split(r'\n(Q\d+[\.:\s]*)', "\n" + full_text)
    
    questions = []
    for i in range(1, len(q_blocks), 2):
        q_label = q_blocks[i]
        q_content = q_blocks[i+1]
        
        q_num_match = re.search(r'\d+', q_label)
        if not q_num_match: continue
        q_num = q_num_match.group(0)
        
        # 1. Find Answer first to help delimit options
        ans_match = re.search(r'(?:Answer|Ans|Correct Answer|Ans-)\s*[:\-\s]*\s*\(?([a-d])\)?', q_content, re.I)
        answer = ans_match.group(1).lower() if ans_match else ""
        
        # 2. Extract Options
        options = {}
        opt_markers = list(re.finditer(r'\(([a-d])\)', q_content, re.I))
        
        # We might have multiple sets of (a)(b)(c)(d) if the question is repeated in explanation
        # We only want the first set
        primary_opts = []
        seen_chars = set()
        for m in opt_markers:
            char = m.group(1).lower()
            if char not in seen_chars:
                primary_opts.append(m)
                seen_chars.add(char)
            if len(seen_chars) == 4:
                break
        
        if len(primary_opts) >= 1:
            for j in range(len(primary_opts)):
                char = primary_opts[j].group(1).lower()
                start = primary_opts[j].end()
                if j < len(primary_opts) - 1:
                    end = primary_opts[j+1].start()
                else:
                    # End of last option is either Answer: or Tip: or Explanation:
                    marker_match = re.search(r'(?:Answer|Ans|Explanation|PT|Tip)[:\-\s]', q_content[start:], re.I)
                    if marker_match:
                        end = start + marker_match.start()
                    else:
                        end = len(q_content)
                options[char] = q_content[start:end].strip().replace('\n', ' ')

        # 3. Extract Question Text
        if primary_opts:
            q_text = q_content[:primary_opts[0].start()].strip().replace('\n', ' ')
        else:
            q_text = q_content.split('Answer:')[0].strip().replace('\n', ' ')

        # 4. Extract Explanation
        # Look for the last "Tip:" or "Explanation:" or "PT:" which contains the real content
        real_exp_match = re.search(r'(?:Tip|Explanation|PT)[:\-\s]+(.*)', q_content, re.I | re.DOTALL)
        if real_exp_match:
            explanation = real_exp_match.group(1).strip()
        else:
            # Fallback: everything after the answer
            if ans_match:
                explanation = q_content[ans_match.end():].strip()
            else:
                explanation = ""
        
        # Clean explanation from trailing question numbers
        explanation = re.split(r'\nQ\d+', explanation)[0].strip()
        explanation = explanation.replace('\n', ' <br> ')

        if q_text and answer:
            subject = "Medicine"
            if int(q_num) > 80: subject = "Pediatrics"
            if paper == "2":
                num_v = int(q_num)
                if num_v <= 40: subject = "Surgery"
                elif num_v <= 80: subject = "OBG"
                else: subject = "PSM"
                
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
            
    return questions


def run_extraction():
    pdf_dir = "new pdf"
    all_extracted = []
    
    files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    for filename in files:
        # Extract year and paper from filename
        # e.g. "new UPSC CMS 2020 paper 1.pdf"
        year_match = re.search(r'20\d{2}', filename)
        paper_match = re.search(r'paper\s*(\d)', filename, re.I)
        
        if year_match and paper_match:
            year = year_match.group(0)
            paper = paper_match.group(1)
            year_q = parse_pdf(os.path.join(pdf_dir, filename), year, paper)
            all_extracted.extend(year_q)
            print(f"Extracted {len(year_q)} questions from {filename}")
        else:
            print(f"Could not parse year/paper from {filename}")
            
    with open('new_fully_extracted_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_extracted, f, indent=2, ensure_ascii=False)
    
    print(f"Total extracted: {len(all_extracted)}")

if __name__ == "__main__":
    run_extraction()
