import json

def get_clinical_subjects():
    try:
        with open('data.js', 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Strip "const mcqData = " and ";"
        if content.startswith('const mcqData = '):
            content = content[len('const mcqData = '):].strip()
            if content.endswith(';'):
                content = content[:-1].strip()
        
        data = json.loads(content)
        subjects = set()
        
        clinical_keywords = [
            'ENT', 'Ophth', 'Radio', 'Derma', 'Ortho', 'Psych', 
            'Anesth', 'Forens', 'Anat', 'Phys', 'Biochem', 'Path', 
            'Micro', 'Pharm', 'Med', 'Surg', 'OBG', 'Ped', 'PSM'
        ]
        
        for q in data:
            # Check subject field
            s = q.get('subject', '').strip()
            if s: subjects.add(s)
            
            # Check topic field (often contains sub-subjects split by /)
            t = q.get('topic', '').strip()
            if '/' in t:
                for part in t.split('/'):
                    subjects.add(part.strip())
            elif t:
                subjects.add(t)
                
            # Check tags
            for tag in q.get('tags', []):
                subjects.add(tag.strip())
        
        # Filter for clinical relevance and reasonable length
        def is_clinical(s):
            if 'Cancelled' in s: return False
            if len(s) > 30: return False
            low = s.lower()
            return any(k.lower() in low for k in clinical_keywords)
            
        filtered = sorted([s for s in subjects if is_clinical(s)])
        return filtered
    except Exception as e:
        return [f"Error: {e}"]

if __name__ == "__main__":
    for s in get_clinical_subjects():
        print(s)
