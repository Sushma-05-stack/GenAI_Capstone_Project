"""
/prompts/* routes: library, versioning, comparison
"""
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
from app.api.deps import get_current_user, require_evaluator
from app.models.user import User
from app.models.prompt import PromptVersion
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptOut, PromptCompareRequest, PromptCompareResult
from app.services.rag.pipeline import run_rag_query
from app.services.evaluation.ragas_engine import evaluate_single

router = APIRouter(prefix="/prompts", tags=["Prompts"])


def _extract_variables(content: str) -> List[str]:
    return list(set(re.findall(r"\{(\w+)\}", content)))


def _prompt_out(p: PromptVersion) -> PromptOut:
    return PromptOut(
        id=str(p.id),
        name=p.name,
        version=p.version,
        content=p.content,
        description=p.description,
        owner_id=p.owner_id,
        is_active=p.is_active,
        tags=p.tags,
        avg_faithfulness=p.avg_faithfulness,
        avg_answer_relevancy=p.avg_answer_relevancy,
        avg_latency_ms=p.avg_latency_ms,
        eval_count=p.eval_count,
        created_at=p.created_at,
    )


@router.post("/", response_model=PromptOut, dependencies=[Depends(require_evaluator)])
async def create_prompt(payload: PromptCreate, current_user: User = Depends(get_current_user)):
    prompt = PromptVersion(
        name=payload.name,
        version=payload.version,
        content=payload.content,
        description=payload.description,
        owner_id=str(current_user.id),
        tags=payload.tags,
        variables=_extract_variables(payload.content),
    )
    await prompt.insert()
    return _prompt_out(prompt)


@router.get("/", response_model=List[PromptOut])
async def list_prompts(
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None),
    active_only: bool = True,
):
    filters = {"owner_id": str(current_user.id)}
    if active_only:
        filters["is_active"] = True
    prompts = await PromptVersion.find(filters).to_list()
    if search:
        prompts = [p for p in prompts if search.lower() in p.name.lower()]
    return [_prompt_out(p) for p in prompts]


@router.get("/{prompt_id}", response_model=PromptOut)
async def get_prompt(prompt_id: str, current_user: User = Depends(get_current_user)):
    prompt = await PromptVersion.get(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return _prompt_out(prompt)


@router.delete("/{prompt_id}", dependencies=[Depends(require_evaluator)])
async def delete_prompt(prompt_id: str, current_user: User = Depends(get_current_user)):
    prompt = await PromptVersion.get(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    if prompt.owner_id != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this prompt")
    await prompt.delete()
    return {"message": "Prompt deleted", "id": prompt_id}


@router.put("/{prompt_id}", response_model=PromptOut, dependencies=[Depends(require_evaluator)])
async def update_prompt(
    prompt_id: str, payload: PromptUpdate, current_user: User = Depends(get_current_user)
):
    prompt = await PromptVersion.get(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    if payload.content is not None:
        prompt.content = payload.content
        prompt.variables = _extract_variables(payload.content)
    if payload.description is not None:
        prompt.description = payload.description
    if payload.tags is not None:
        prompt.tags = payload.tags
    if payload.is_active is not None:
        prompt.is_active = payload.is_active
    prompt.updated_at = datetime.now(timezone.utc)
    await prompt.save()
    return _prompt_out(prompt)


@router.post("/compare", dependencies=[Depends(require_evaluator)])
async def compare_prompts(
    payload: PromptCompareRequest, current_user: User = Depends(get_current_user)
):
    from app.models.dataset import Dataset

    prompt_a = await PromptVersion.get(payload.prompt_a_id)
    prompt_b = await PromptVersion.get(payload.prompt_b_id)
    dataset = await Dataset.get(payload.dataset_id)

    if not prompt_a or not prompt_b:
        raise HTTPException(status_code=404, detail="One or both prompts not found")
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    qa_pairs = dataset.qa_pairs[: payload.max_questions]
    results_a, results_b = [], []

    for qa in qa_pairs:
        question = qa.get("question", "")
        ground_truth = qa.get("ground_truth")

        # Eval with prompt A
        resp_a = await run_rag_query(
            question=question, dataset_id=payload.dataset_id,
            provider=payload.provider, model_name=payload.model_name,
            prompt_version_id=payload.prompt_a_id,
        )
        eval_a = await evaluate_single(question, resp_a.answer, resp_a.contexts, ground_truth)

        # Eval with prompt B
        resp_b = await run_rag_query(
            question=question, dataset_id=payload.dataset_id,
            provider=payload.provider, model_name=payload.model_name,
            prompt_version_id=payload.prompt_b_id,
        )
        eval_b = await evaluate_single(question, resp_b.answer, resp_b.contexts, ground_truth)

        results_a.append({"faithfulness": eval_a.faithfulness, "relevancy": eval_a.answer_relevancy,
                           "latency": resp_a.latency_ms, "cost": resp_a.cost_usd or 0})
        results_b.append({"faithfulness": eval_b.faithfulness, "relevancy": eval_b.answer_relevancy,
                           "latency": resp_b.latency_ms, "cost": resp_b.cost_usd or 0})

    def safe_avg(lst, key):
        vals = [v[key] for v in lst if v[key] is not None]
        return sum(vals) / len(vals) if vals else 0.0

    avg_faith_a = safe_avg(results_a, "faithfulness")
    avg_faith_b = safe_avg(results_b, "faithfulness")
    avg_rel_a = safe_avg(results_a, "relevancy")
    avg_rel_b = safe_avg(results_b, "relevancy")
    avg_lat_a = safe_avg(results_a, "latency")
    avg_lat_b = safe_avg(results_b, "latency")
    avg_cost_a = safe_avg(results_a, "cost")
    avg_cost_b = safe_avg(results_b, "cost")

    score_a = (avg_faith_a + avg_rel_a) / 2
    score_b = (avg_faith_b + avg_rel_b) / 2
    winner = "A" if score_a > score_b else ("B" if score_b > score_a else "tie")

    return {
        "prompt_a": _prompt_out(prompt_a),
        "prompt_b": _prompt_out(prompt_b),
        "avg_faithfulness_a": round(avg_faith_a, 4),
        "avg_faithfulness_b": round(avg_faith_b, 4),
        "avg_relevancy_a": round(avg_rel_a, 4),
        "avg_relevancy_b": round(avg_rel_b, 4),
        "faithfulness_diff": round(avg_faith_b - avg_faith_a, 4),
        "relevancy_diff": round(avg_rel_b - avg_rel_a, 4),
        "latency_diff_ms": round(avg_lat_b - avg_lat_a, 2),
        "cost_diff_usd": round(avg_cost_b - avg_cost_a, 6),
        "winner": winner,
        "questions_evaluated": len(qa_pairs),
    }
