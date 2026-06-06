"""
Evaluation Run Orchestrator
Coordinates RAG queries + RAGAS scoring for a full dataset evaluation.
"""
import asyncio
import statistics
from datetime import datetime, timezone
from app.models.evaluation import EvaluationRun, EvaluationResult, EvalStatus
from app.models.dataset import Dataset
from app.services.rag.pipeline import run_rag_query
from app.services.evaluation.ragas_engine import evaluate_single
from app.core.logging import logger


async def run_evaluation(run: EvaluationRun) -> EvaluationRun:
    run.status = EvalStatus.RUNNING
    run.started_at = datetime.now(timezone.utc)
    await run.save()
    logger.info("Evaluation started", run_id=str(run.id), dataset_id=run.dataset_id)

    # ── Load dataset ──────────────────────────────────────────────────────────
    dataset = await Dataset.get(run.dataset_id)
    if not dataset:
        return await _fail(run, f"Dataset {run.dataset_id} not found")

    qa_pairs = dataset.qa_pairs or []

    if not qa_pairs:
        return await _fail(
            run,
            f"Dataset '{dataset.name}' has 0 QA pairs. "
            "Add QA pairs to the dataset first (Datasets → select dataset → Add QA Pairs)."
        )

    # Apply max_questions limit
    max_q = run.metadata.get("max_questions")
    if max_q:
        qa_pairs = qa_pairs[:int(max_q)]

    run.total_questions = len(qa_pairs)
    await run.save()
    logger.info("Processing QA pairs", run_id=str(run.id), total=run.total_questions)

    # ── Metric accumulators ───────────────────────────────────────────────────
    faithfulness_scores, relevancy_scores = [], []
    precision_scores,    recall_scores    = [], []
    hallucination_scores, retrieval_scores = [], []
    latencies, costs = [], []
    errors = 0

    for i, qa in enumerate(qa_pairs):
        question    = (qa.get("question")    or "").strip()
        ground_truth = (qa.get("ground_truth") or "").strip() or None

        if not question:
            logger.warning("Skipping empty question", idx=i)
            continue

        try:
            # ── RAG Query ─────────────────────────────────────────────────────
            logger.info("RAG query", idx=i + 1, total=run.total_questions, q=question[:60])
            rag_resp = await run_rag_query(
                question=question,
                dataset_id=run.dataset_id,
                provider=run.provider,
                model_name=run.model_name,
                prompt_version_id=run.prompt_version_id,
                query_id=str(run.id),
            )

            # ── RAGAS scoring ─────────────────────────────────────────────────
            logger.info("RAGAS scoring", idx=i + 1, answer_len=len(rag_resp.answer))
            ragas = await evaluate_single(
                question=question,
                answer=rag_resp.answer,
                contexts=rag_resp.contexts,
                ground_truth=ground_truth,
            )

            # ── Persist result ────────────────────────────────────────────────
            result = EvaluationResult(
                run_id          = str(run.id),
                question        = question,
                answer          = rag_resp.answer,
                ground_truth    = ground_truth,
                contexts        = rag_resp.contexts,
                retrieved_chunks= rag_resp.retrieved_chunks,
                faithfulness      = ragas.faithfulness,
                answer_relevancy  = ragas.answer_relevancy,
                context_precision = ragas.context_precision,
                context_recall    = ragas.context_recall,
                hallucination_risk= ragas.hallucination_risk,
                retrieval_quality = ragas.retrieval_quality,
                latency_ms  = rag_resp.latency_ms,
                cost_usd    = rag_resp.cost_usd,
                model_used  = rag_resp.model_used,
                provider_used = rag_resp.provider_used,
                fallback_used = rag_resp.fallback_used,
                langsmith_trace_url = rag_resp.langsmith_trace_url,
            )
            await result.insert()

            # Accumulate
            if ragas.faithfulness       is not None: faithfulness_scores.append(ragas.faithfulness)
            if ragas.answer_relevancy   is not None: relevancy_scores.append(ragas.answer_relevancy)
            if ragas.context_precision  is not None: precision_scores.append(ragas.context_precision)
            if ragas.context_recall     is not None: recall_scores.append(ragas.context_recall)
            if ragas.hallucination_risk is not None: hallucination_scores.append(ragas.hallucination_risk)
            if ragas.retrieval_quality  is not None: retrieval_scores.append(ragas.retrieval_quality)
            if rag_resp.latency_ms: latencies.append(rag_resp.latency_ms)
            if rag_resp.cost_usd:   costs.append(rag_resp.cost_usd)

            run.completed_questions = i + 1
            await run.save()
            logger.info(
                "Question evaluated",
                idx=i + 1, total=run.total_questions,
                faithfulness=ragas.faithfulness,
                relevancy=ragas.answer_relevancy,
                hall_risk=ragas.hallucination_risk,
            )

        except Exception as e:
            errors += 1
            logger.error("Question evaluation failed", idx=i, error=str(e)[:300])
            # Store a failed result so the user can see what went wrong
            try:
                await EvaluationResult(
                    run_id   = str(run.id),
                    question = question,
                    answer   = f"[ERROR: {str(e)[:200]}]",
                    ground_truth = ground_truth,
                    model_used   = run.model_name,
                    provider_used = run.provider,
                ).insert()
            except Exception:
                pass
            run.completed_questions = i + 1
            await run.save()
            continue

    # ── Aggregate ─────────────────────────────────────────────────────────────
    def safe_mean(lst):
        return round(statistics.mean(lst), 4) if lst else None

    run.avg_faithfulness      = safe_mean(faithfulness_scores)
    run.avg_answer_relevancy  = safe_mean(relevancy_scores)
    run.avg_context_precision = safe_mean(precision_scores)
    run.avg_context_recall    = safe_mean(recall_scores)
    run.avg_hallucination_risk= safe_mean(hallucination_scores)
    run.avg_retrieval_quality = safe_mean(retrieval_scores)
    run.avg_latency_ms        = safe_mean(latencies)
    run.total_cost_usd        = round(sum(costs), 6) if costs else None
    run.status      = EvalStatus.COMPLETED
    run.completed_at = datetime.now(timezone.utc)
    if errors > 0:
        run.error_message = f"{errors}/{run.total_questions} questions failed — partial results available"
    await run.save()

    logger.info(
        "Evaluation complete",
        run_id=str(run.id),
        faithfulness=run.avg_faithfulness,
        relevancy=run.avg_answer_relevancy,
        hallucination=run.avg_hallucination_risk,
        errors=errors,
    )
    return run


async def _fail(run: EvaluationRun, msg: str) -> EvaluationRun:
    run.status = EvalStatus.FAILED
    run.error_message = msg
    await run.save()
    logger.error("Evaluation failed", run_id=str(run.id), reason=msg)
    return run
