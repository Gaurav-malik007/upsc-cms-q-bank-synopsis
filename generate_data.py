import fitz
import re
import json
import os
import glob

def extract_mcqs_from_file(pdf_path):
    print(f"Reading PDF: {pdf_path}")
    
    # Extract Year and Paper number from filename
    # E.g., "upsc cms 2024 paper 1.pdf" or "2023_paper2.pdf"
    filename = os.path.basename(pdf_path).lower()
    
    year_match = re.search(r'(19|20)\d{2}', filename)
    year = int(year_match.group(0)) if year_match else "Unknown Year"
    
    paper_match = re.search(r'paper\s*(\d)', filename)
    paper_num = int(paper_match.group(1)) if paper_match else 1
    
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
        
    full_text = full_text.replace('\n', ' ')
    q_splits = re.split(r'Q\d+\.', full_text)
    
    mcqs = []
    
    for q_block in q_splits[1:]:
        try:
            opt_match = re.search(r'\(a\)(.*?)\(b\)(.*?)\(c\)(.*?)\(d\)(.*?)(?=Answer:)', q_block)
            if not opt_match:
                continue
                
            question_text = q_block[:opt_match.start()].strip()
            opt_a = opt_match.group(1).strip()
            opt_b = opt_match.group(2).strip()
            opt_c = opt_match.group(3).strip()
            opt_d = opt_match.group(4).strip()
            
            ans_match = re.search(r'Answer:\s*\(([a-d])\)', q_block)
            answer = ans_match.group(1) if ans_match else ""
            
            exp_match = re.search(r'Explanation & Tip:(.*?)$', q_block[ans_match.end() if ans_match else opt_match.end():].split('   For More High-Yield')[0])
            
            if exp_match:
                explanation = exp_match.group(1).strip()
            else:
                exp_match2 = re.search(r'Explanation & Tip:(.*?)$', q_block)
                if exp_match2:
                    explanation = exp_match2.group(1).strip()
                else:
                    exp_split = q_block.split('Answer: (' + answer + ')')
                    if len(exp_split) > 1:
                        explanation = exp_split[1].replace('Explanation & Tip:', '').strip()
                    else:
                        explanation = "No explanation provided."
            
            # Clean explanation
            explanation = re.sub(r'For More High-Yield.*?(?=@itsgauravmalikk\s*\d*|@itsgauravmalikk)', '', explanation, flags=re.IGNORECASE)
            explanation = re.sub(r'@itsgauravmalikk\s*\d*', '', explanation, flags=re.IGNORECASE).strip()

            # Subject logic based on User info:
            # Paper 1: Medicine, Paediatrics
            # Paper 2: PSM, Surgery, Obstetrics & Gynaecology
            text_for_search = question_text + explanation
            subject = "Unknown"
            
            if paper_num == 1:
                if re.search(r'neonate|pediatric|child|infant|puberty|vaccine', text_for_search, re.IGNORECASE):
                    subject = "Paediatrics"
                else:
                    subject = "Medicine"
            else:
                if re.search(r'psm|preventive|epidemiology|community|health|incidence|prevalence', text_for_search, re.IGNORECASE):
                    subject = "PSM"
                elif re.search(r'obs|gynae|pregnancy|uterus|cervix|placenta', text_for_search, re.IGNORECASE):
                    subject = "Obstetrics & Gynaecology"
                else:
                    subject = "Surgery"
                
            mcq = {
                "question": question_text,
                "options": {
                    "a": opt_a,
                    "b": opt_b,
                    "c": opt_c,
                    "d": opt_d
                },
                "answer": answer,
                "explanation": explanation,
                "subject": subject,
                "year": year,
                "paper": paper_num
            }
            mcqs.append(mcq)
            
        except Exception as e:
            print(f"Error parsing block: {e}")
            continue

    return mcqs

if __name__ == "__main__":
    all_mcqs = []
    pdf_files = glob.glob("*.pdf")
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        exit()
        
    for pdf_file in pdf_files:
        mcqs = extract_mcqs_from_file(pdf_file)
        all_mcqs.extend(mcqs)
        print(f"Extracted {len(mcqs)} questions from {pdf_file}.")
        
    print(f"Total questions extracted: {len(all_mcqs)}")
    
    js_content = f"const mcqData = {json.dumps(all_mcqs, indent=4)};"
    
    with open("data.js", "w", encoding='utf-8') as f:
        f.write(js_content)
    print("Saved all extracted data to data.js")
