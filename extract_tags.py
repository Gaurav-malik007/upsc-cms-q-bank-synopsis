import json
import os

data_file = r'c:\Users\deepa\Desktop\cms\data.js'
with open(data_file, 'r', encoding='utf-8') as f:
    content = f.read().strip()

if content.startswith('const mcqData = '):
    json_str = content[len('const mcqData = '):].strip()
    if json_str.endswith(';'):
        json_str = json_str[:-1].strip()
    
    data = json.loads(json_str)
    subjects = set()
    topics = set()
    tags = set()
    
    for q in data:
        if 'subject' in q: subjects.add(q['subject'])
        if 'topic' in q: topics.add(q['topic'])
        if 'tags' in q: 
            for t in q['tags']:
                tags.add(t)
    
    print("Unique Subjects:")
    print(sorted(list(subjects)))
    print("\nUnique Topics:")
    print(sorted(list(topics)))
    print("\nUnique Tags:")
    print(sorted(list(tags)))
else:
    print("Could not find mcqData in data.js")
