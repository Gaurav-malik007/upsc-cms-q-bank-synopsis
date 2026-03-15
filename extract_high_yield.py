import fitz
import re
import json
import os

PDF_DIR = r"c:\Users\deepa\Desktop\cms\pyq pdf"
OUTPUT_DIR = "high_yield_extraction"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# regex patterns
# [Subject: ...] Q1. Text... (a) Opt A (b) Opt B (c) Opt C (d) Opt D Answer: (x) Explanation & Tip: Expl
Q_PATTERN = re.compile(r'(?:\[Subject:\s*(.*?)\s*\|\s*Topic:\s*(.*?)\])?\s*Q(\d+)\.\s*(.*?)\s*\(a\)\s*(.*?)\s?\(b\)\s*(.*?)\s?\(c\)\s*(.*?)\s?\(d\)\s*(.*?)\s?Answer:\s*[\(\{\[]?([a-d])[\)\}\]]?(.*?)(?=(?:\[Subject:.*?\])?\s*Q\d+\.|$)', re.DOTALL | re.I)

def extract_from_pdf(filepath, year, paper):
    doc = fitz.open(filepath)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    
    # Clean up artifacts like "For More High-Yield..."
    full_text = re.sub(r'For More High-Yield Medical Notes & Updates.*?@itsgauravmalikk', '', full_text, flags=re.DOTALL | re.I)
    
    matches = Q_PATTERN.findall(full_text)
    mcqs = []
    
    # Subject Mapping to App Tags
    subject_map = {
        "Medicine": "Medicine",
        "Surgery": "Surgery",
        "Pediatrics": "Pediatrics",
        "Obstetrics & Gynecology": "OBGYN",
        "OBG": "OBGYN",
        "PSM": "PSM",
        "Community Medicine": "PSM",
        "Orthopaedics": "Orthopaedics",
        "Psychiatry": "Psychiatry"
    }

    for m in matches:
        raw_sub, raw_topic, q_num, q_text, opt_a, opt_b, opt_c, opt_d, ans, expl = m
        
        # Determine Tag
        tag = "Medicine" # Default
        if raw_sub:
            found = False
            for pdf_sub, app_sub in subject_map.items():
                if pdf_sub.lower() in raw_sub.lower():
                    tag = app_sub
                    found = True
                    break
        elif paper == "2":
            # Paper 2 usually Surgery/OBG/Peds
            # Add general paper 2 tag if no headers
            tag = "Surgery"
        
        # Clean up the tip/explanation
        expl = expl.strip()
        if expl.lower().startswith("explanation & tip:"):
            expl = expl[18:].strip()
        elif expl.lower().startswith("| tip:"):
            expl = expl[6:].strip()
        
        mcqs.append({
            "id": f"UPSC_{year}_P{paper}_Q{q_num}",
            "num": q_num,
            "question": q_text.strip(),
            "options": {
                "a": opt_a.strip(),
                "b": opt_b.strip(),
                "c": opt_c.strip(),
                "d": opt_d.strip()
            },
            "answer": ans.lower().strip(),
            "explanation": expl,
            "year": year,
            "paper": paper,
            "tags": [tag]
        })
    
    return mcqs

def run_all():
    all_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    total_extracted = 0
    
    for filename in all_files:
        path = os.path.join(PDF_DIR, filename)
        # Extract year and paper from filename
        # Examples: "UPSC CMS 2021 PAPER 1.pdf", "Upsc cms 2020 paper 2.pdf"
        match = re.search(r'(\d{4}).*?(\d)', filename)
        if match:
            year = match.group(1)
            paper = match.group(2)
            results = extract_from_pdf(path, year, paper)
            
            output_file = os.path.join(OUTPUT_DIR, f"{year}_P{paper}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            
            print(f"Extracted {len(results)} questions from {filename}")
            total_extracted += len(results)
    
    print(f"Total extracted: {total_extracted}")

if __name__ == "__main__":
    run_all()
