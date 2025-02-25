import re
from typing import List

def clean_text(text: str) -> str:
    text = re.sub(r'[^A-Za-z0-9\s]', '', text)  # Remove special characters
    return text.lower().strip()
