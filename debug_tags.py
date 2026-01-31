
import re

filename = r'e:\BIGBURRY\SERVICES\Ashiq hr module\hr_module\core\templates\core\summary.html'

with open(filename, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f"Read {len(lines)} lines")

stack = []
for i, line in enumerate(lines):
    # Find all tags
    tags = re.findall(r'{%\s*(if|endif|for|endfor|block|endblock|with|endwith)\b', line)
    for tag in tags:
        if tag in ['if', 'for', 'block', 'with']:
            stack.append((tag, i + 1))
        elif tag in ['endif', 'endfor', 'endblock', 'endwith']:
            if not stack:
                print(f"Error: Unexpected {{% {tag} %}} at line {i+1}")
                continue
            last_tag, last_line = stack.pop()
            expected = 'end' + last_tag
            if tag != expected:
                print(f"Error: Mismatch at line {i+1}. Found {{% {tag} %}}, expected {{% {expected} %}} for {{% {last_tag} %}} from line {last_line}")
                # Put it back to maybe sync up later? No, usually fatal.
                
if stack:
    print("Unclosed tags:")
    for tag, line_num in stack:
        print(f"  {{% {tag} %}} at line {line_num}")
