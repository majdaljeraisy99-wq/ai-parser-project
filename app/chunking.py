import re
from utils import detect_language


def detect_chunking_strategy(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lang = detect_language(text)

    heading_count = 0
    short_line_count = 0

    for line in lines:
        if len(line) < 80:
            short_line_count += 1

        is_heading = (
            line.endswith(":")
            or line.startswith("#")
            or bool(re.match(r"^\d+[\.\-]", line))
            or (lang == "en" and ("chapter" in line.lower() or "section" in line.lower()))
            or (lang == "ar" and ("الفصل" in line or "القسم" in line or "عنوان" in line))
        )

        if len(line) < 120 and is_heading:
            heading_count += 1

    paragraph_lengths = [len(p) for p in text.split("\n") if p.strip()]
    variance_proxy = 0
    if paragraph_lengths:
        avg_len = sum(paragraph_lengths) / len(paragraph_lengths)
        variance_proxy = sum(abs(x - avg_len) for x in paragraph_lengths) / len(paragraph_lengths)

    if heading_count >= 2 or variance_proxy > 250 or short_line_count > 8:
        return "dynamic"

    return "fixed"


def fixed_chunking(text: str, chunk_size: int = 800, overlap: int = 120):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def dynamic_chunking(text: str, max_chunk_size: int = 1200):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 <= max_chunk_size:
            current_chunk += para + "\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def chunk_document(text: str):
    strategy = detect_chunking_strategy(text)

    if strategy == "dynamic":
        chunks = dynamic_chunking(text)
    else:
        chunks = fixed_chunking(text)

    return strategy, chunks