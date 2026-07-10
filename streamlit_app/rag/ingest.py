"""Turn a file (or the static disease knowledge base) into embedded chunks in
a FAISS collection."""

import json
import uuid

from ..config import KB_PATH
from . import vector_store
from .chunking import chunk_text
from .loaders import load_any


def ingest_document(collection_name: str, filename: str, data: bytes) -> int:
    text = load_any(filename, data)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    collection = vector_store.get_collection(collection_name)
    doc_id = uuid.uuid4().hex[:8]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filename, "chunk": i} for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def ingest_kb_if_empty() -> int:
    collection = vector_store.get_collection(vector_store.KB_COLLECTION)
    if collection.count() > 0:
        return 0

    with open(KB_PATH, encoding="utf-8") as f:
        kb = json.load(f)

    documents, ids, metadatas = [], [], []
    for entry in kb:
        measures = "; ".join(entry.get("precautionary_measures") or [])
        text = (
            f"{entry['disease_name']} (crop: {entry.get('affected_crop', 'unknown')}, "
            f"healthy: {entry.get('is_healthy')}).\n"
            f"Symptoms: {entry.get('symptoms', '')}\n"
            f"Precautionary measures: {measures}"
        )
        documents.append(text)
        ids.append(entry["class_name"])
        metadatas.append({"source": "disease_knowledge_base.json", "class_name": entry["class_name"]})

    collection.add(documents=documents, ids=ids, metadatas=metadatas)
    return len(documents)
