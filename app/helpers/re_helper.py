import re

def get_formatted_text(text, pattern):
    
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return text