
data_path = r'c:\Users\deepa\Desktop\cms\data.js'

with open(data_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Precise fix for the identified malformation
old_segment = '"explanation": "In pharmacology, medications with the suffix \'-tinib\' (e.g., Imatinib, Erlotinib, Gefitinib) belong to the class of Tyrosine Kinase Inhibitors. They are targeted therapies used extensively in oncology to block signaling pathways that drive cancer cell growth."-tinib\\" is a Tyrosine Kinase Inhibitor."'
new_segment = '"explanation": "In pharmacology, medications with the suffix \'-tinib\' (e.g., Imatinib, Erlotinib, Gefitinib) belong to the class of Tyrosine Kinase Inhibitors. They are targeted therapies used extensively in oncology to block signaling pathways that drive cancer cell growth. \'-tinib\' is a Tyrosine Kinase Inhibitor."'

if old_segment in content:
    print("Fixing segment...")
    content = content.replace(old_segment, new_segment)
else:
    # Try with double escaped backslash just in case
    old_segment_2 = old_segment.replace('\\"', '\\\\"')
    if old_segment_2 in content:
        print("Fixing segment (alt escape)...")
        content = content.replace(old_segment_2, new_segment)
    else:
        # Fallback to fuzzy match
        import re
        content = re.sub(r'drive cancer cell growth\."-tinib\\"', r'drive cancer cell growth. \'-tinib\'', content)
        print("Applied fuzzy fix.")

with open(data_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done.")
