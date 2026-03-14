import os

data_file = r'c:\Users\deepa\Desktop\cms\data.js'
with open(data_file, 'r', encoding='utf-8') as f:
    content = f.read()

# The broken part:
broken_str = '"explanation": "The UNAIDS 90-90-90 strategy is a global target to end AIDS. By 2020, 90% of all people living with HIV should know their status, 90% of all people with diagnosed HIV infection should receive sustained antiretroviral therapy (ART), and 90% of all people receiving ART should have viral suppression."Graph\\" means writing. Dyslexia is reading; Dyscalculia is math.",'
fixed_str = '"explanation": "Mnemonic: \'Graph\' means writing. Dyslexia is reading; Dyscalculia is math.",'

if broken_str in content:
    new_content = content.replace(broken_str, fixed_str)
    with open(data_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed data.js successfully.")
else:
    # Try with different escaping if needed
    print("Broken string not found exactly. Testing alternative.")
    # The output I saw had Graph\" which in python string would be Graph\\"
    # Let's try matching a portion
    target = 'viral suppression."Graph\\" means writing'
    if target in content:
        print("Found partial match, attempting fix.")
        # Replace the whole block
        # Start of explanation is a bit before
        start_idx = content.find('The UNAIDS 90-90-90 strategy')
        end_idx = content.find('Dyscalculia is math.', start_idx) + len('Dyscalculia is math.')
        if start_idx != -1 and end_idx != -1:
            mangled_block = content[start_idx:end_idx]
            print(f"Replacing: {mangled_block}")
            new_content = content.replace(mangled_block, "Mnemonic: 'Graph' means writing. Dyslexia is reading; Dyscalculia is math.")
            with open(data_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Fixed data.js via partial match successfully.")
        else:
            print("Could not find start/end of mangled block.")
    else:
        print("Partial match also not found.")
