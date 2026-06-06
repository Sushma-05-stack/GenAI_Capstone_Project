"""
RAG Evaluation Dashboard - FastAPI Application Entry Point
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.mongodb import connect_db, disconnect_db
from app.api.routes import auth, users, datasets, rag, evaluation, prompts, models, feedback, dashboard, reports, security


# Setup logging
setup_logging()

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("Starting RAG Eval Dashboard", env=settings.APP_ENV)
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    await connect_db()
    yield
    await disconnect_db()
    logger.info("RAG Eval Dashboard shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise RAG Evaluation Dashboard with Multi-LLM Fallback and RAGAS",
    version="1.0.0",
    docs_url="/docs",    # always enabled so we can test on Render
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow configured origins + common Vercel/Render patterns
cors_origins = settings.cors_origins_list
# Always allow localhost for development
if "http://localhost:3000" not in cors_origins:
    cors_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # allow all Vercel preview URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")
app.include_router(evaluation.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(models.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(security.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    """Root endpoint — confirms API is running."""
    return {"message": f"{settings.APP_NAME} API is running", "docs": "/docs"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )
