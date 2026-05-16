import sys

try:
    with open('test_out.txt', 'r', encoding='utf-16le') as f:
        text = f.read()
except Exception as e:
    try:
        with open('test_out.txt', 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

for line in text.split('\n'):
    if 'fail' in line.lower():
        print(line.strip())
