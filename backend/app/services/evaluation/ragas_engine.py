"""
RAGAS Evaluation Engine
Computes all 6 metrics:
  - Faithfulness          (LLM judge: is answer grounded in context?)
  - Answer Relevancy      (embedding similarity: is answer relevant to question?)
  - Context Precision     (LLM judge: are retrieved chunks relevant?)
  - Context Recall        (LLM judge: does context cover ground truth?)
  - Hallucination Risk    (derived: 1 - faithfulness)
  - Retrieval Quality     (derived: F1 of precision & recall)

Judge LLM priority: Groq llama-3.3-70b → OpenAI gpt-4o-mini
Embeddings priority: OpenAI text-embedding-3-small → ChromaDB ONNX
Every RAGAS call is traced in LangSmith when key is configured.
"""
import asyncio
from typing import List, Optional
from dataclasses import dataclass
from app.core.config import settings
from app.core.logging import logger

# ── Singletons ─────────────────────────────────────────────────────────────────
_judge_llm = None
_embeddings = None


@dataclass
class RAGASResult:
    faithfulness:       Optional[float] = None
    answer_relevancy:   Optional[float] = None
    context_precision:  Optional[float] = None
    context_recall:     Optional[float] = None
    hallucination_risk: Optional[float] = None
    retrieval_quality:  Optional[float] = None


# ── Helpers ────────────────────────────────────────────────────────────────────
def _hallucination(faith: Optional[float]) -> Optional[float]:
    return round(1.0 - faith, 4) if faith is not None else None


def _f1(prec: Optional[float], rec: Optional[float]) -> Optional[float]:
    if prec is None or rec is None:
        return None
    return round(2 * prec * rec / (prec + rec), 4) if (prec + rec) > 0 else 0.0


def _get_judge_llm():
    global _judge_llm
    if _judge_llm is not None:
        return _judge_llm

    # Groq is fast and doesn't need OpenAI quota
    if settings.GROQ_API_KEY and len(settings.GROQ_API_KEY) > 10:
        try:
            from langchain_groq import ChatGroq
            _judge_llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=settings.GROQ_API_KEY,
                temperature=0,
            )
            logger.info("RAGAS judge LLM: Groq llama-3.3-70b-versatile")
            return _judge_llm
        except Exception as e:
            logger.warning("Groq init failed", error=str(e))

    # OpenAI fallback
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10:
        try:
            from langchain_openai import ChatOpenAI
            _judge_llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0,
            )
            logger.info("RAGAS judge LLM: OpenAI gpt-4o-mini")
            return _judge_llm
        except Exception as e:
            logger.warning("OpenAI init failed", error=str(e))

    raise RuntimeError(
        "No LLM available for RAGAS scoring. "
        "Please set GROQ_API_KEY or OPENAI_API_KEY in .env"
    )


def _get_embeddings():
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    # OpenAI best quality
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10:
        try:
            from langchain_openai import OpenAIEmbeddings
            _embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY,
            )
            logger.info("RAGAS embeddings: OpenAI text-embedding-3-small")
            return _embeddings
        except Exception as e:
            logger.warning("OpenAI embeddings failed", error=str(e))

    # Local fallback via ChromaDB ONNX wrapped in langchain
    try:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        class ChromaLangchainEmbeddings:
            """Adapter: wraps ChromaDB's ONNX ef for LangChain/RAGAS."""
            def __init__(self):
                self._ef = DefaultEmbeddingFunction()

            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                return [list(v) for v in self._ef(texts)]

            def embed_query(self, text: str) -> List[float]:
                return list(self._ef([text])[0])

        _embeddings = ChromaLangchainEmbeddings()
        logger.info("RAGAS embeddings: ChromaDB ONNX (all-MiniLM-L6-v2)")
        return _embeddings
    except Exception as e:
        logger.warning("Local embeddings failed", error=str(e))
        return None


# ── Main evaluation function ───────────────────────────────────────────────────
async def evaluate_single(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None,
) -> RAGASResult:
    """
    Run all RAGAS metrics on one QA result.
    Returns RAGASResult with scores between 0 and 1.

    faithfulness  = how grounded the answer is in the context
    answer_relevancy = how relevant the answer is to the question
    context_precision = % of retrieved chunks that are relevant
    context_recall  = % of ground truth covered by retrieved context
    hallucination_risk = 1 - faithfulness
    retrieval_quality = F1(precision, recall)
    """
    if not answer or not answer.strip():
        logger.warning("Empty answer — RAGAS skipped", question=question[:60])
        return RAGASResult()

    if not contexts:
        logger.warning("Empty contexts — RAGAS skipped", question=question[:60])
        return RAGASResult()

    try:
        from datasets import Dataset as HFDataset
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness as ragas_faithfulness,
            answer_relevancy as ragas_answer_relevancy,
            context_precision as ragas_context_precision,
            context_recall as ragas_context_recall,
        )

        # Build HuggingFace dataset
        data: dict = {
            "question": [question],
            "answer":   [answer],
            "contexts": [contexts],
        }
        if ground_truth and ground_truth.strip():
            data["ground_truth"] = [ground_truth]

        hf_ds = HFDataset.from_dict(data)

        # Get judge LLM and embeddings
        llm = _get_judge_llm()
        emb = _get_embeddings()

        # Select metrics
        # faithfulness + answer_relevancy always run
        # context_precision + context_recall need ground_truth
        metrics = [ragas_faithfulness, ragas_answer_relevancy]
        if ground_truth and ground_truth.strip():
            metrics += [ragas_context_precision, ragas_context_recall]

        # Inject LLM and embeddings into each metric instance
        for m in metrics:
            m.llm = llm
            if hasattr(m, "embeddings") and emb is not None:
                m.embeddings = emb

        logger.info(
            "RAGAS scoring",
            question=question[:60],
            answer_len=len(answer),
            contexts=len(contexts),
            metrics=len(metrics),
            has_ground_truth=bool(ground_truth),
        )

        # Run synchronously in executor (RAGAS is sync)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: evaluate(hf_ds, metrics=metrics),
        )

        row = result.to_pandas().iloc[0].to_dict()
        logger.info(
            "RAGAS scores computed",
            faithfulness=row.get("faithfulness"),
            answer_relevancy=row.get("answer_relevancy"),
            context_precision=row.get("context_precision"),
            context_recall=row.get("context_recall"),
        )

        faith = row.get("faithfulness")
        rel   = row.get("answer_relevancy")
        prec  = row.get("context_precision")
        rec   = row.get("context_recall")

        return RAGASResult(
            faithfulness      = round(faith, 4) if faith is not None else None,
            answer_relevancy  = round(rel,   4) if rel   is not None else None,
            context_precision = round(prec,  4) if prec  is not None else None,
            context_recall    = round(rec,   4) if rec   is not None else None,
            hallucination_risk= _hallucination(faith),
            retrieval_quality = _f1(prec, rec),
        )

    except Exception as e:
        logger.error("RAGAS scoring failed — using heuristic fallback", error=str(e)[:400])
        return _heuristic_scores(question, answer, contexts, ground_truth)


# ── Heuristic fallback (when RAGAS itself fails) ───────────────────────────────
def _heuristic_scores(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str],
) -> RAGASResult:
    """
    Word-overlap heuristics — not as accurate as RAGAS LLM judging
    but always returns numeric values so evaluation runs don't produce NULLs.
    """
    ans_words = set(answer.lower().split())
    ctx_text  = " ".join(contexts).lower()
    ctx_words = set(ctx_text.split())
    q_words   = set(question.lower().split()) - {
        "what", "is", "the", "a", "an", "how", "why",
        "when", "where", "does", "do", "can", "i",
    }

    # Faithfulness: fraction of answer words found in context
    overlap = len(ans_words & ctx_words)
    faith = round(min(overlap / max(len(ans_words), 1), 1.0), 4)

    # Penalise refusals
    refusals = ["not contain", "not enough", "not found",
                "no information", "cannot answer", "do not contain"]
    if any(r in answer.lower() for r in refusals):
        faith = round(faith * 0.3, 4)

    # Answer relevancy: question keywords in answer
    rel_num = len(q_words & ans_words) / max(len(q_words), 1)
    relevancy = round(min(rel_num * 1.5, 1.0), 4)

    # Context precision & recall (only with ground truth)
    ctx_prec = ctx_rec = None
    if ground_truth and ground_truth.strip():
        gt_words = set(ground_truth.lower().split())
        ctx_prec = round(min(len(q_words & ctx_words) / max(len(q_words), 1), 1.0), 4)
        ctx_rec  = round(min(len(gt_words & ctx_words) / max(len(gt_words), 1), 1.0), 4)

    logger.info("Heuristic RAGAS scores",
                faithfulness=faith, relevancy=relevancy,
                ctx_prec=ctx_prec, ctx_rec=ctx_rec)

    return RAGASResult(
        faithfulness      = faith,
        answer_relevancy  = relevancy,
        context_precision = ctx_prec,
        context_recall    = ctx_rec,
        hallucination_risk= _hallucination(faith),
        retrieval_quality = _f1(ctx_prec, ctx_rec),
    )
