"""
Embedding generation and ChromaDB indexing.

Priority order:
  1. OpenAI text-embedding-3-small  (best quality, needs API key + quota)
  2. ChromaDB default embedding fn  (all-MiniLM-L6-v2 via chromadb, no extra deps)
"""
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.db.chromadb import get_or_create_collection
from app.services.document.chunker import TextChunk

BATCH_SIZE = 100

# ChromaDB's built-in embedding function (uses ONNX, no Keras/TF needed)
_chroma_ef = None


def _get_chroma_ef():
    global _chroma_ef
    if _chroma_ef is None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        _chroma_ef = DefaultEmbeddingFunction()
        logger.info("ChromaDB default embedding function loaded (all-MiniLM-L6-v2 via ONNX)")
    return _chroma_ef


async def _embed_with_openai(texts: List[str]) -> List[List[float]]:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        response = await client.embeddings.create(
            model="text-embedding-3-small", input=batch
        )
        all_embeddings.extend([item.embedding for item in response.data])
        logger.info("OpenAI embeddings generated", count=len(batch))
    return all_embeddings


def _embed_with_chroma(texts: List[str]) -> List[List[float]]:
    """Use ChromaDB's bundled ONNX embedding function — zero extra dependencies."""
    ef = _get_chroma_ef()
    result = ef(texts)
    return [list(v) for v in result]


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Try OpenAI first; fall back to ChromaDB's built-in ONNX model on any failure.
    """
    if settings.OPENAI_API_KEY:
        try:
            return await _embed_with_openai(texts)
        except Exception as e:
            logger.warning(
                "OpenAI embedding failed — using local ONNX fallback",
                error=str(e)[:150],
            )
    logger.info("Using ChromaDB ONNX embeddings (all-MiniLM-L6-v2)")
    return _embed_with_chroma(texts)


async def index_chunks(
    collection_name: str,
    chunks: List[TextChunk],
    document_id: str,
    dataset_id: str,
    extra_metadata: Dict[str, Any] = {},
) -> List[str]:
    """Embed chunks and upsert into ChromaDB. Returns ChromaDB IDs."""
    texts = [c.content for c in chunks]
    embeddings = await embed_texts(texts)

    collection = get_or_create_collection(collection_name)
    ids = [f"{document_id}_chunk_{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "dataset_id": dataset_id,
            "chunk_index": c.chunk_index,
            "token_estimate": c.token_estimate,
            **extra_metadata,
        }
        for c in chunks
    ]

    for i in range(0, len(chunks), BATCH_SIZE):
        collection.upsert(
            ids=ids[i: i + BATCH_SIZE],
            embeddings=embeddings[i: i + BATCH_SIZE],
            documents=texts[i: i + BATCH_SIZE],
            metadatas=metadatas[i: i + BATCH_SIZE],
        )

    logger.info("Chunks indexed", collection=collection_name, count=len(chunks))
    return ids


async def semantic_search(
    collection_name: str,
    query: str,
    top_k: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Search ChromaDB. Returns [{id, content, score, metadata}, ...]"""
    query_embedding = await embed_texts([query])
    collection = get_or_create_collection(collection_name)

    count = collection.count()
    if count == 0:
        logger.warning("ChromaDB collection empty", collection=collection_name)
        return []

    actual_top_k = min(top_k, count)
    kwargs: Dict[str, Any] = {
        "query_embeddings": query_embedding,
        "n_results": actual_top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if filter_metadata:
        kwargs["where"] = filter_metadata

    results = collection.query(**kwargs)

    chunks = []
    if results["ids"] and results["ids"][0]:
        for idx, chunk_id in enumerate(results["ids"][0]):
            chunks.append({
                "id": chunk_id,
                "content": results["documents"][0][idx],
                "score": round(1 - results["distances"][0][idx], 4),
                "metadata": results["metadatas"][0][idx],
            })
    return chunks
