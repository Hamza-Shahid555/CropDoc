"""Top-k similarity search over one or more FAISS collections — the Research
Agent's only job is calling this."""

from . import vector_store


def search(collection_name: str, query: str, top_k: int = 4) -> list[dict]:
    collection = vector_store.get_collection(collection_name)
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))
    hits = []
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({"text": doc, "metadata": meta, "distance": dist})
    return hits


def search_multi(collection_names: list[str], query: str, top_k: int = 4) -> list[dict]:
    all_hits = []
    for name in collection_names:
        all_hits.extend(search(name, query, top_k=top_k))
    all_hits.sort(key=lambda h: h["distance"])
    return all_hits[:top_k]
