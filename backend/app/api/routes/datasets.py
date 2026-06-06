"""
/datasets/* routes: CRUD, upload, QA management
"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
from app.api.deps import get_current_user, require_evaluator
from app.models.user import User
from app.models.dataset import Dataset, DatasetStatus
from app.models.document import Document
from app.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetOut, DatasetListResponse
from app.services.document.pipeline import process_document
from app.security.audit import log_event
from app.models.audit import AuditAction
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/datasets", tags=["Datasets"])
ALLOWED_TYPES = {"pdf", "docx", "txt", "csv"}


def _dataset_out(d: Dataset) -> DatasetOut:
    return DatasetOut(
        id=str(d.id),
        name=d.name,
        description=d.description,
        owner_id=d.owner_id,
        version=d.version,
        status=d.status,
        file_count=d.file_count,
        qa_count=d.qa_count,
        tags=d.tags,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


async def _index_qa_pairs_to_chroma(dataset: Dataset):
    """
    Index QA pairs (questions + ground truths) into ChromaDB so they
    can be retrieved even when no documents have been uploaded yet.
    """
    if not dataset.qa_pairs:
        return
    try:
        from app.db.chromadb import get_or_create_collection
        from app.services.document.embedder import embed_texts

        collection_name = f"dataset_{str(dataset.id)}"
        collection = get_or_create_collection(collection_name)

        texts, ids, metadatas = [], [], []
        for i, qa in enumerate(dataset.qa_pairs):
            # Index question + ground truth as one searchable chunk
            content = f"Q: {qa.get('question', '')}\nA: {qa.get('ground_truth', '')}"
            texts.append(content)
            ids.append(f"qa_{str(dataset.id)}_{i}")
            metadatas.append({
                "source": "qa_pair",
                "dataset_id": str(dataset.id),
                "question": qa.get("question", "")[:200],
            })

        embeddings = await embed_texts(texts)
        collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        logger.info("QA pairs indexed to ChromaDB", dataset_id=str(dataset.id), count=len(texts))
    except Exception as e:
        logger.error("Failed to index QA pairs", error=str(e))


@router.post("/", response_model=DatasetOut, dependencies=[Depends(require_evaluator)])
async def create_dataset(
    payload: DatasetCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    dataset = Dataset(
        name=payload.name,
        description=payload.description,
        owner_id=str(current_user.id),
        tags=payload.tags,
        qa_pairs=[qa.model_dump() for qa in (payload.qa_pairs or [])],
        qa_count=len(payload.qa_pairs or []),
        status=DatasetStatus.READY,
    )
    await dataset.insert()

    # Index QA pairs into ChromaDB in background
    if dataset.qa_pairs:
        background_tasks.add_task(_index_qa_pairs_to_chroma, dataset)

    await log_event(
        action=AuditAction.CREATE_DATASET,
        user_id=str(current_user.id),
        resource=str(dataset.id),
    )
    return _dataset_out(dataset)


@router.get("/", response_model=DatasetListResponse)
async def list_datasets(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tag: Optional[str] = None,
):
    filter_dict: dict = {"owner_id": str(current_user.id), "is_deleted": False}
    if search:
        filter_dict["name"] = {"$regex": search, "$options": "i"}
    if tag:
        filter_dict["tags"] = tag

    total = await Dataset.find(filter_dict).count()
    datasets = (
        await Dataset.find(filter_dict)
        .sort("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list()
    )
    return DatasetListResponse(
        datasets=[_dataset_out(d) for d in datasets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{dataset_id}", response_model=DatasetOut)
async def get_dataset(dataset_id: str, current_user: User = Depends(get_current_user)):
    dataset = await Dataset.get(dataset_id)
    if not dataset or dataset.is_deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return _dataset_out(dataset)


@router.put("/{dataset_id}", response_model=DatasetOut, dependencies=[Depends(require_evaluator)])
async def update_dataset(
    dataset_id: str,
    payload: DatasetUpdate,
    current_user: User = Depends(get_current_user),
):
    dataset = await Dataset.get(dataset_id)
    if not dataset or dataset.is_deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if payload.name:
        dataset.name = payload.name
    if payload.description is not None:
        dataset.description = payload.description
    if payload.tags is not None:
        dataset.tags = payload.tags
    dataset.updated_at = datetime.now(timezone.utc)
    await dataset.save()
    return _dataset_out(dataset)


@router.delete("/{dataset_id}", dependencies=[Depends(require_evaluator)])
async def delete_dataset(dataset_id: str, current_user: User = Depends(get_current_user)):
    dataset = await Dataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset.is_deleted = True
    dataset.updated_at = datetime.now(timezone.utc)
    await dataset.save()
    await log_event(
        action=AuditAction.DELETE_DATASET,
        user_id=str(current_user.id),
        resource=dataset_id,
    )
    return {"message": "Dataset deleted"}


@router.post("/{dataset_id}/upload", dependencies=[Depends(require_evaluator)])
async def upload_document(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    dataset = await Dataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Supported: {sorted(ALLOWED_TYPES)}",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB). Max: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    upload_dir = Path(settings.UPLOAD_DIR) / dataset_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        dataset_id=dataset_id,
        owner_id=str(current_user.id),
        filename=file.filename,
        file_type=ext,
        file_size=len(content),
        storage_path=str(file_path),
    )
    await doc.insert()

    dataset.file_count += 1
    dataset.status = DatasetStatus.PROCESSING
    await dataset.save()

    background_tasks.add_task(process_document, doc)

    await log_event(
        action=AuditAction.UPLOAD_DOCUMENT,
        user_id=str(current_user.id),
        resource=str(doc.id),
        details={"filename": file.filename, "size_mb": round(size_mb, 2)},
    )
    return {
        "message": "File uploaded and processing started",
        "document_id": str(doc.id),
    }


@router.post("/{dataset_id}/qa-pairs", dependencies=[Depends(require_evaluator)])
async def add_qa_pairs(
    dataset_id: str,
    qa_pairs: List[dict],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    dataset = await Dataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    dataset.qa_pairs.extend(qa_pairs)
    dataset.qa_count = len(dataset.qa_pairs)
    dataset.updated_at = datetime.now(timezone.utc)
    await dataset.save()

    # Re-index new QA pairs
    background_tasks.add_task(_index_qa_pairs_to_chroma, dataset)

    return {"message": f"Added {len(qa_pairs)} QA pairs", "total": dataset.qa_count}


@router.post("/{dataset_id}/reindex", dependencies=[Depends(require_evaluator)])
async def reindex_dataset(
    dataset_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Force re-index all QA pairs for a dataset into ChromaDB."""
    dataset = await Dataset.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    background_tasks.add_task(_index_qa_pairs_to_chroma, dataset)
    return {"message": "Re-indexing started in background", "qa_count": dataset.qa_count}
