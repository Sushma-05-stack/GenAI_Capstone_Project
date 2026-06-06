from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logging import logger

# Import all document models
from app.models.user import User
from app.models.dataset import Dataset
from app.models.document import Document, Chunk
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.models.prompt import PromptVersion
from app.models.model_result import ModelResult
from app.models.audit import AuditLog
from app.models.feedback import Feedback
from app.models.fallback import FallbackEvent
from app.models.metrics import SystemMetric

_client: AsyncIOMotorClient = None


async def connect_db():
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=_client[settings.MONGODB_DB_NAME],
        document_models=[
            User,
            Dataset,
            Document,
            Chunk,
            EvaluationRun,
            EvaluationResult,
            PromptVersion,
            ModelResult,
            AuditLog,
            Feedback,
            FallbackEvent,
            SystemMetric,
        ],
    )
    logger.info("MongoDB connected", db=settings.MONGODB_DB_NAME)


async def disconnect_db():
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB disconnected")
