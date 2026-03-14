
data_path = r'c:\Users\deepa\Desktop\cms\data.js'

with open(data_path, 'r', encoding='utf-8') as f:
    content = f.read()

target_id = '"id": "2023_29"'
pos = content.find(target_id)
if pos != -1:
    # Print 500 characters around it
    print(content[pos:pos+1000])
else:
    print("ID not found")
