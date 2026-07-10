"""Research Agent: no LLM call of its own — just embeds the query and runs
similarity search against the always-on disease knowledge base plus (if a
chat session has uploaded documents) that session's private collection."""

from ..rag import retriever, vector_store


def research(query: str, session_id: int | None = None, top_k: int = 4) -> list[dict]:
    collections = [vector_store.KB_COLLECTION]
    if session_id is not None:
        session_coll = vector_store.get_collection(vector_store.session_collection_name(session_id))
        if session_coll.count() > 0:
            collections.append(vector_store.session_collection_name(session_id))
    return retriever.search_multi(collections, query, top_k=top_k)


def format_context(hits: list[dict]) -> str:
    if not hits:
        return ""
    blocks = []
    for h in hits:
        source = h["metadata"].get("source", "knowledge base")
        blocks.append(f"[source: {source}]\n{h['text']}")
    return "\n\n".join(blocks)
