import re

def clean_log(text: str) -> str:
    text = re.sub(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?", " TIMESTAMP ", text)
    text = re.sub(r"\b\d+\b", " NUMBER ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()
