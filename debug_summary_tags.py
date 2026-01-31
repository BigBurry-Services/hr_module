
import re
import sys

filename = r'e:\BIGBURRY\SERVICES\Ashiq hr module\hr_module\core\templates\core\summary.html'
output_file = r'e:\BIGBURRY\SERVICES\Ashiq hr module\hr_module\tag_debug_output.txt'

print(f"Analyzing {filename}...")

try:
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except Exception as e:
    print(f"Failed to open file: {e}")
    sys.exit(1)

stack = []
with open(output_file, 'w', encoding='utf-8') as out:
    out.write(f"Analyzing {len(lines)} lines...\n")
    
    for i, line in enumerate(lines):
        line_num = i + 1
        # Find all tags in the line
        # We need to find them in order. re.finditer is good.
        matches = re.finditer(r'{%\s*(if|endif|for|endfor|block|endblock|with|endwith|while|endwhile)\b', line)
        
        for match in matches:
            tag = match.group(1)
            
            if tag in ['if', 'for', 'block', 'with', 'while']:
                stack.append((tag, line_num))
                out.write(f"Line {line_num}: Pushed {tag}. Stack depth: {len(stack)}\n")
            
            elif tag in ['endif', 'endfor', 'endblock', 'endwith', 'endwhile']:
                if not stack:
                    out.write(f"ERROR: Unexpected {{% {tag} %}} at line {line_num}\n")
                    continue
                
                last_tag, last_line = stack.pop()
                expected = 'end' + last_tag
                # Special case handling if needed, but usually strictly mapped
                
                if tag != expected:
                    out.write(f"ERROR: Mismatch at line {line_num}. Found {{% {tag} %}}, expected {{% {expected} %}} for {{% {last_tag} %}} opened at line {last_line}\n")
                    # Put it back to continue analysis?
                    # stack.append((last_tag, last_line)) 
                else:
                    out.write(f"Line {line_num}: Closed {last_tag} from line {last_line}\n")

    if stack:
        out.write("\nUNCLOSED TAGS DETECTED:\n")
        for tag, line_num in stack:
            out.write(f"  {{% {tag} %}} at line {line_num}\n")
    else:
        out.write("\nNo unclosed tags found.\n")

print(f"Analysis complete. Check {output_file}")
