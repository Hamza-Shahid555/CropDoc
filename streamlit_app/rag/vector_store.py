"""FAISS-backed vector store (with a JSON metadata sidecar) instead of Chroma.

Chroma's bundled native HNSW extension reliably segfaults in this environment
(collection.add() crashes even for a single document) — a known class of
issue where chromadb's compiled binary is incompatible with the numpy<2 pin
this project needs for torch/Grad-CAM. FAISS has no such conflict and is an
explicitly acceptable alternative per the RAG design, so the vector store
layer uses it instead. The public interface (get_collection/query shape)
mirrors Chroma's so the rest of the RAG code barely changes.

Each "collection" is a directory of two files: index.faiss (the vector index)
and meta.json (the parallel list of {id, document, metadata} records, whose
positions line up with the FAISS index rows)."""

import json
from pathlib import Path

import faiss
import numpy as np
from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, VECTOR_DIR

KB_COLLECTION = "disease_knowledge_base"

_openai_client = None


def _client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def embed_texts(texts: list[str]) -> np.ndarray:
    resp = _client().embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=texts)
    vecs = [d.embedding for d in resp.data]
    return np.array(vecs, dtype="float32")


class FaissCollection:
    def __init__(self, name: str):
        self.name = name
        self.dir_path = VECTOR_DIR / name
        self.dir_path.mkdir(parents=True, exist_ok=True)
        self.index_path = self.dir_path / "index.faiss"
        self.meta_path = self.dir_path / "meta.json"
        self._index = None
        self._meta: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self.meta_path.is_file():
            self._meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        if self.index_path.is_file():
            self._index = faiss.read_index(str(self.index_path))

    def _persist(self) -> None:
        faiss.write_index(self._index, str(self.index_path))
        self.meta_path.write_text(json.dumps(self._meta), encoding="utf-8")

    def count(self) -> int:
        return len(self._meta)

    def add(self, documents: list[str], ids: list[str], metadatas: list[dict]) -> None:
        vecs = embed_texts(documents)
        if self._index is None:
            self._index = faiss.IndexFlatL2(vecs.shape[1])
        self._index.add(vecs)
        for doc_id, doc, meta in zip(ids, documents, metadatas):
            self._meta.append({"id": doc_id, "document": doc, "metadata": meta})
        self._persist()

    def query(self, query_texts: list[str], n_results: int = 4) -> dict:
        if not self._meta or self._index is None:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        qvecs = embed_texts(query_texts)
        k = min(n_results, len(self._meta))
        distances, indices = self._index.search(qvecs, k)

        docs, metas, dists = [], [], []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < 0:
                continue
            record = self._meta[idx]
            docs.append(record["document"])
            metas.append(record["metadata"])
            dists.append(float(dist))
        return {"documents": [docs], "metadatas": [metas], "distances": [dists]}


_collections: dict[str, FaissCollection] = {}


def get_collection(name: str) -> FaissCollection:
    if name not in _collections:
        _collections[name] = FaissCollection(name)
    return _collections[name]


def session_collection_name(session_id: int) -> str:
    return f"session_{session_id}_docs"


def delete_collection(name: str) -> None:
    import shutil

    _collections.pop(name, None)
    dir_path = VECTOR_DIR / name
    if dir_path.exists():
        shutil.rmtree(dir_path, ignore_errors=True)
