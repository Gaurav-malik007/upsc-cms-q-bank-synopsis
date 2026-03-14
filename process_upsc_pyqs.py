import fitz
import json
import os
import re

IMAGES_DIR = "images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_cms_pdf(pdf_path):
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    filename_lower = os.path.basename(pdf_path).lower()
    year_match = re.search(r'(20\d{2})', filename_lower)
    year = year_match.group(1) if year_match else "Unknown"
    
    # Guess subject from filename if header is missing
    fallback_subject = "UPSC CMS"
    if "paper 1" in filename_lower:
        fallback_subject = "Medicine & Paediatrics"
    elif "paper 2" in filename_lower:
        fallback_subject = "Surgery, OBG & PSM"

    all_mcqs = []
    
    full_text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        full_text += page.get_text("text") + "\n"

    lines = full_text.split('\n')
    
    curr_mcq = None
    curr_state = None # 'question', 'answer_tip'
    
    # regex for subject/topic line: [Subject: Medicine | Topic: Cardiology] Q17.
    header_pattern = r'\[Subject:\s*(.*?)\s*\|\s*Topic:\s*(.*?)\]\s*Q(.*?)\.'
    # regex for bare question start: Q17. or Q53/54. or Q54(b).
    bare_q_pattern = r'^Q([\d\(\)\/a-zA-Z]+)\.'
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check if new question starts with header
        header_match = re.match(header_pattern, line)
        if header_match:
            if curr_mcq:
                process_mcq_content(curr_mcq)
                all_mcqs.append(curr_mcq)
            
            subject = clean_text(header_match.group(1))
            topic = clean_text(header_match.group(2))
            q_num = header_match.group(3)
            
            curr_mcq = create_mcq_obj(year, q_num, subject, topic, line[header_match.end():].strip())
            curr_state = 'question'
            continue
            
        # Check if new question starts WITHOUT header
        bare_q_match = re.match(bare_q_pattern, line)
        if bare_q_match:
            if curr_mcq:
                process_mcq_content(curr_mcq)
                all_mcqs.append(curr_mcq)
            
            q_num = bare_q_match.group(1)
            curr_mcq = create_mcq_obj(year, q_num, fallback_subject, "General", line[bare_q_match.end():].strip())
            curr_state = 'question'
            continue

        if curr_mcq:
            # Check for Cancelled Question
            if "Cancelled Question" in line or "officially cancelled" in line.lower():
                curr_mcq["question"] = "Cancelled Question"
                curr_mcq["explanation"] = "This question was officially cancelled by the UPSC."
                curr_mcq["answer"] = "n/a"
                curr_mcq["options"] = {}
                curr_state = 'answer_tip'
                continue

            # Match options: (a) Text (b) Text ...
            option_matches = list(re.finditer(r'\(([a-d])\)\s*(.*?)(?=\s*\([a-d]\)|$|\s*Answer:|\s*Select the correct)', line, re.IGNORECASE))
            for om in option_matches:
                opt_letter = om.group(1).lower()
                opt_text = om.group(2).strip()
                if opt_letter not in curr_mcq['options'] or not curr_mcq['options'][opt_letter]:
                    curr_mcq['options'][opt_letter] = opt_text
            
            # Check for Answer line: "Answer: (b)" or "Answer: (b) | Tip:"
            ans_match = re.search(r'Answer:\s*\(([a-d])\)', line, re.IGNORECASE)
            if ans_match:
                curr_mcq['answer'] = ans_match.group(1).lower()
                tip_match = re.search(r'(?:Explanation\s*&\s*)?Tip:\s*(.*)', line, re.IGNORECASE)
                if tip_match:
                    curr_mcq["explanation"] = clean_text(tip_match.group(1))
                curr_state = 'answer_tip'
            else:
                tip_match = re.search(r'(?:Explanation\s*&\s*)?Tip:\s*(.*)', line, re.IGNORECASE)
                if tip_match:
                    curr_mcq["explanation"] = clean_text(tip_match.group(1))
                    curr_state = 'answer_tip'
                else:
                    if curr_state == 'question':
                        curr_mcq["question_blob"] += " " + line
                    elif curr_state == 'answer_tip':
                        curr_mcq["explanation"] += " " + line

    if curr_mcq:
        process_mcq_content(curr_mcq)
        all_mcqs.append(curr_mcq)
        
    print(f"Extracted {len(all_mcqs)} questions from {os.path.basename(pdf_path)}")
    if len(all_mcqs) != 120:
        print(f"WARNING: Expected 120 questions, but found {len(all_mcqs)} in {os.path.basename(pdf_path)}")
    return all_mcqs

def create_mcq_obj(year, q_num, subject, topic, blob):
    return {
        "id": f"{year}_{q_num}_{subject[:3]}", # include subject to avoid id collisions across papers
        "num": q_num,
        "question_blob": blob,
        "options": {},
        "answer": "",
        "explanation": "",
        "subject": subject,
        "topic": topic,
        "year": year,
        "tags": [year, "PYQ", subject]
    }

def process_mcq_content(mcq):
    blob = mcq.pop("question_blob", "")
    # Improved pattern that accounts for options mashed together
    opt_pattern = r'\(([a-d])\)'
    parts = re.split(opt_pattern, blob)
    
    # The first part is always the question text
    mcq["question"] = clean_text(parts[0])
    
    # Merge options found in the blob
    blob_options = {}
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            key = parts[i].lower()
            val = clean_text(parts[i+1])
            # Only use blob option if it's longer/better than what we might have found in line-by-line
            blob_options[key] = val
    
    # Merge: If we already have an option from the loop, keep it unless blob is markedly better
    for k, v in blob_options.items():
        if k not in mcq["options"] or len(v) > len(mcq["options"][k]):
            mcq["options"][k] = v

def process_all_pdfs():
    pdf_dir = "pyq pdf"
    all_results = []
    
    if not os.path.exists(pdf_dir):
        print(f"Directory {pdf_dir} not found.")
        return
        
    for filename in sorted(os.listdir(pdf_dir)):
        if filename.endswith(".pdf"):
            res = parse_cms_pdf(os.path.join(pdf_dir, filename))
            all_results.extend(res)
            
    with open("data.js", "w", encoding="utf-8") as f:
        f.write(f"const mcqData = {json.dumps(all_results, indent=2)};\n")
    print(f"Saved total {len(all_results)} questions to data.js")

if __name__ == "__main__":
    process_all_pdfs()
