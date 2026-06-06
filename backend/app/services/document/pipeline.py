"""
Full document processing pipeline:
Upload → Extract → Clean → Chunk → Embed → Store
"""
import os
import shutil
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger
from app.models.document import Document, Chunk, DocumentStatus
from app.services.document.loader import extract_text
from app.services.document.chunker import chunk_text
from app.services.document.embedder import index_chunks
from datetime import datetime, timezone


async def process_document(document: Document) -> Document:
    """
    Run full pipeline for a document.
    Updates document status in MongoDB.
    """
    doc_id = str(document.id)
    try:
        document.status = DocumentStatus.PROCESSING
        document.updated_at = datetime.now(timezone.utc)
        await document.save()

        # 1. Extract text
        logger.info("Extracting text", doc_id=doc_id, file_type=document.file_type)
        raw_text, extract_meta = await extract_text(document.storage_path, document.file_type)

        # 2. Chunk text
        chunks = chunk_text(raw_text, chunk_size=512, chunk_overlap=64)
        logger.info("Chunked document", doc_id=doc_id, chunks=len(chunks))

        # 3. Determine ChromaDB collection name (one per dataset)
        collection_name = f"dataset_{document.dataset_id}"
        document.chroma_collection = collection_name

        # 4. Embed and index
        chroma_ids = await index_chunks(
            collection_name=collection_name,
            chunks=chunks,
            document_id=doc_id,
            dataset_id=document.dataset_id,
            extra_metadata={
                "filename": document.filename,
                "file_type": document.file_type,
            },
        )

        # 5. Persist Chunk documents in MongoDB
        chunk_docs = [
            Chunk(
                document_id=doc_id,
                dataset_id=document.dataset_id,
                content=c.content,
                chunk_index=c.chunk_index,
                chroma_id=chroma_ids[c.chunk_index],
                token_count=c.token_estimate,
            )
            for c in chunks
        ]
        await Chunk.insert_many(chunk_docs)

        # 6. Update document
        document.chunk_count = len(chunks)
        document.status = DocumentStatus.INDEXED
        document.metadata.update(extract_meta)
        document.updated_at = datetime.now(timezone.utc)
        await document.save()

        logger.info("Document processing complete", doc_id=doc_id, chunks=len(chunks))
        return document

    except Exception as e:
        logger.error("Document processing failed", doc_id=doc_id, error=str(e))
        document.status = DocumentStatus.ERROR
        document.error_message = str(e)
        document.updated_at = datetime.now(timezone.utc)
        await document.save()
        raise
