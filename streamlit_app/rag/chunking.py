"""Paragraph-aware recursive text splitter. No LangChain dependency needed for
something this small — split on blank lines first, then hard-wrap anything
still too long, and stitch chunks back together with a bit of overlap so
context isn't lost at chunk boundaries."""


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    units: list[str] = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            units.append(para)
        else:
            for i in range(0, len(para), chunk_size - overlap):
                units.append(para[i : i + chunk_size])

    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = f"{current}\n\n{unit}" if current else unit
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            tail = current[-overlap:] if current and overlap else ""
            current = f"{tail}\n\n{unit}" if tail else unit
    if current:
        chunks.append(current)

    return chunks
