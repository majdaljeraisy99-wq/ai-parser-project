import re


ARABIC_DIACRITICS_PATTERN = r"[\u0617-\u061A\u064B-\u0652]"


def detect_language(text: str) -> str:
    arabic_chars = re.findall(r'[\u0600-\u06FF]', text or "")
    english_chars = re.findall(r'[A-Za-z]', text or "")

    if len(arabic_chars) >= len(english_chars):
        return "ar"
    return "en"


def normalize_arabic(text: str, keep_diacritics: bool = False) -> str:
    if not text:
        return ""

    text = re.sub(r"[ـ]+", "", text)
    text = re.sub(r"[أإآا]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ؤ", "و", text)
    text = re.sub(r"ئ", "ي", text)
    text = re.sub(r"ة", "ه", text)

    if not keep_diacritics:
        text = re.sub(ARABIC_DIACRITICS_PATTERN, "", text)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_english(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^\w\s\-\:\.\,\?\'\"]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text(text: str, keep_diacritics: bool = False) -> str:
    lang = detect_language(text)
    if lang == "ar":
        return normalize_arabic(text, keep_diacritics=keep_diacritics)
    return normalize_english(text)


def contains_diacritics(text: str) -> bool:
    return bool(re.search(ARABIC_DIACRITICS_PATTERN, text or ""))


def safe_preview(text: str, max_len: int = 220) -> str:
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."