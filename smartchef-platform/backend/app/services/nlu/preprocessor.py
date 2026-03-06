"""Text preprocessor: cleaning, language detection, truncation."""
import re


MAX_INPUT_LENGTH = 500


def detect_language(text: str) -> str:
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_alpha = len(re.findall(r'[a-zA-Z]', text))
    if chinese_chars == 0 and total_alpha > 0:
        return "en"
    return "zh"


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:，。！？；：、""''（）\-+%℃°]', '', text)
    return text


def preprocess(text: str) -> tuple[str, str, bool]:
    """Returns (cleaned_text, language, was_truncated)."""
    cleaned = clean_text(text)
    language = detect_language(cleaned)
    truncated = False

    if len(cleaned) > MAX_INPUT_LENGTH:
        cleaned = cleaned[:MAX_INPUT_LENGTH]
        truncated = True

    return cleaned, language, truncated
