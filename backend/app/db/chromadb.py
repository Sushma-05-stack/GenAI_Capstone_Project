"""
ChromaDB client.
- Uses chromadb.CloudClient when CHROMA_API_KEY + CHROMA_TENANT + CHROMA_DATABASE set.
- Falls back to local PersistentClient automatically and silently.
"""
import chromadb
from app.core.config import settings
from app.core.logging import logger

_chroma_client: chromadb.ClientAPI = None
_mode: str = "unset"


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client, _mode

    if _chroma_client is not None:
        return _chroma_client

    # ── Try ChromaDB Cloud ─────────────────────────────────────────────────────
    if settings.use_cloud_chroma:
        try:
            client = chromadb.CloudClient(
                tenant=settings.CHROMA_TENANT,
                database=settings.CHROMA_DATABASE,
                api_key=settings.CHROMA_API_KEY,
            )
            # Validate the connection
            client.list_collections()
            _chroma_client = client
            _mode = "cloud"
            logger.info(
                "ChromaDB Cloud connected",
                tenant=settings.CHROMA_TENANT,
                database=settings.CHROMA_DATABASE,
            )
            return _chroma_client
        except Exception as e:
            logger.warning(
                "ChromaDB Cloud unavailable — using local storage. "
                "Check that your CHROMA_TENANT matches your ChromaDB Cloud dashboard.",
                error=str(e)[:150],
            )

    # ── Local PersistentClient fallback ────────────────────────────────────────
    _chroma_client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )
    _mode = "local"
    logger.info("ChromaDB local storage active", path=settings.CHROMA_PERSIST_DIR)
    return _chroma_client


def get_mode() -> str:
    return _mode


def get_or_create_collection(name: str, metadata: dict = None) -> chromadb.Collection:
    return get_chroma_client().get_or_create_collection(
        name=name,
        metadata=metadata or {"hnsw:space": "cosine"},
    )


def delete_collection(name: str):
    try:
        get_chroma_client().delete_collection(name)
        logger.info("ChromaDB collection deleted", collection=name)
    except Exception as e:
        logger.warning("ChromaDB delete skipped", collection=name, error=str(e)[:80])


def reset_client():
    """Force re-init — call this after fixing CHROMA_TENANT in .env."""
    global _chroma_client, _mode
    _chroma_client = None
    _mode = "unset"
    logger.info("ChromaDB client reset — will reconnect on next request")
