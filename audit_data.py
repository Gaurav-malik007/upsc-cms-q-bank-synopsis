import re
import json
from collections import Counter

def audit_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to find all year and paper fields
    years = re.findall(r'"year":\s*"([^"]+)"', content)
    papers = re.findall(r'"paper":\s*"([^"]+)"', content)
    
    # Find IDs to verify
    ids = re.findall(r'"id":\s*"([^"]+)"', content)
    
    stats = Counter()
    for y, p in zip(years, papers):
        stats[f"{y} P{p}"] += 1
    
    print(json.dumps(dict(stats), indent=2))
    print(f"Total entries: {len(ids)}")

if __name__ == "__main__":
    audit_data("data.js")
