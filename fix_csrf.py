import os

def fix_csrf():
    template_dir = 'c:/Users/GUNAVARDHAN/Desktop/qr_prescription_system/templates'
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # We need to find <form method="POST" ...> and see if it has CSRF
                import re
                
                # regex to find form tags with POST method
                form_pattern = re.compile(r'(<form[^>]*method=[\'"]POST[\'"][^>]*>)', re.IGNORECASE)
                
                def replacement(match):
                    form_tag = match.group(1)
                    # If this specific form string is already followed by csrf, skip
                    # We can just inject it right after the tag if we do a simple replace,
                    # but wait, there could be multiple forms.
                    
                    return form_tag + '\n    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'

                # To avoid double injecting, let's just do a naive check:
                # If there's a POST form but NO csrf_token and NO hidden_tag in the entire file,
                # this is risky if there are multiple forms.
                # Let's just do a manual replace using the pattern.
                new_content = form_pattern.sub(replacement, content)
                
                # Now we need to remove duplicates if they already had it.
                # Actually, a better way is to split by form_pattern.
                parts = form_pattern.split(content)
                if len(parts) > 1:
                    reconstructed = [parts[0]]
                    modified = False
                    for i in range(1, len(parts), 2):
                        form_tag = parts[i]
                        body = parts[i+1] if i+1 < len(parts) else ""
                        
                        # Check the first few characters of the body for csrf
                        if 'csrf_token' not in body and 'hidden_tag()' not in body:
                            reconstructed.append(form_tag + '\n    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">\n')
                            reconstructed.append(body)
                            modified = True
                        else:
                            reconstructed.append(form_tag)
                            reconstructed.append(body)
                    
                    if modified:
                        print(f"Fixed CSRF in {filepath}")
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write("".join(reconstructed))

if __name__ == '__main__':
    fix_csrf()
