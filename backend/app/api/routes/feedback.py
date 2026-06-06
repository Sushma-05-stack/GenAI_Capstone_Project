"""
/feedback/* routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.api.deps import get_current_user
from app.models.user import User
from app.models.feedback import Feedback, FeedbackType
from app.models.evaluation import EvaluationResult

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackSubmit(BaseModel):
    result_id: str
    feedback_type: FeedbackType
    rating: Optional[int] = None  # 1-5
    comment: Optional[str] = None
    is_hallucination: bool = False
    is_retrieval_issue: bool = False


@router.post("/")
async def submit_feedback(payload: FeedbackSubmit, current_user: User = Depends(get_current_user)):
    result = await EvaluationResult.get(payload.result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation result not found")

    if payload.rating and (payload.rating < 1 or payload.rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    feedback = Feedback(
        result_id=payload.result_id,
        run_id=result.run_id,
        user_id=str(current_user.id),
        feedback_type=payload.feedback_type,
        rating=payload.rating,
        comment=payload.comment,
        is_hallucination=payload.is_hallucination,
        is_retrieval_issue=payload.is_retrieval_issue,
    )
    await feedback.insert()
    return {"message": "Feedback submitted", "feedback_id": str(feedback.id)}


@router.get("/run/{run_id}")
async def get_feedback_for_run(run_id: str, current_user: User = Depends(get_current_user)):
    feedback = await Feedback.find(Feedback.run_id == run_id).to_list()
    total = len(feedback)
    ratings = [f.rating for f in feedback if f.rating]
    hallucination_flags = sum(1 for f in feedback if f.is_hallucination)
    retrieval_issues = sum(1 for f in feedback if f.is_retrieval_issue)
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    return {
        "run_id": run_id,
        "total_feedback": total,
        "avg_rating": avg_rating,
        "hallucination_flags": hallucination_flags,
        "retrieval_issues": retrieval_issues,
        "feedback": [
            {
                "id": str(f.id),
                "result_id": f.result_id,
                "feedback_type": f.feedback_type,
                "rating": f.rating,
                "comment": f.comment,
                "is_hallucination": f.is_hallucination,
                "is_retrieval_issue": f.is_retrieval_issue,
                "created_at": f.created_at,
            }
            for f in feedback
        ],
    }
