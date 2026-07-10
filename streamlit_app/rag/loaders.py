"""Extract plain text from an uploaded file's raw bytes, dispatched by extension.
Kept separate from chunking/embedding so new formats are a one-function addition."""

import io
from pathlib import Path

import pandas as pd
from docx import Document as DocxDocument
from pypdf import PdfReader


def load_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def load_docx(data: bytes) -> str:
    doc = DocxDocument(io.BytesIO(data))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def load_text(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def load_csv(data: bytes) -> str:
    df = pd.read_csv(io.BytesIO(data))
    lines = []
    for _, row in df.iterrows():
        lines.append(", ".join(f"{col}: {row[col]}" for col in df.columns))
    return "\n".join(lines)


_LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".txt": load_text,
    ".md": load_text,
    ".csv": load_csv,
}


def load_any(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    loader = _LOADERS.get(ext)
    if loader is None:
        raise ValueError(f"Unsupported document type: {ext or filename}")
    return loader(data)


SUPPORTED_EXTENSIONS = list(_LOADERS.keys())
