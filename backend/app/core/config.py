from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────────
    APP_NAME: str = "RAG Eval Dashboard"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── MongoDB ────────────────────────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "rageval"

    # ── ChromaDB — cloud keys (api.trychroma.com) ─────────────────────────────
    CHROMA_API_KEY:  Optional[str] = None   # ck-...
    CHROMA_TENANT:   Optional[str] = None   # UUID
    CHROMA_DATABASE: Optional[str] = None   # e.g. "rag-eval-dashboard"
    CHROMA_HOST:     str = "localhost"
    CHROMA_PORT:     int = 8001
    CHROMA_PERSIST_DIR: str = "./chroma_store"   # local fallback path

    # ── OpenAI ─────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL:   str = "gpt-4o"

    # ── Gemini ─────────────────────────────────────────────────────────────────
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL:   str = "gemini-1.5-pro"

    # ── Groq ───────────────────────────────────────────────────────────────────
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL:   str = "llama-3.3-70b-versatile"

    # ── Anthropic ──────────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"

    # ── LangSmith — reads LANGSMITH_* names from .env ─────────────────────────
    LANGSMITH_API_KEY:  Optional[str] = None   # lsv2_pt_...
    LANGSMITH_PROJECT:  str = "rag-eval-dashboard"
    LANGSMITH_TRACING:  bool = True
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # ── CORS ───────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    # ── Rate limiting ──────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── File uploads ──────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    # ── Derived properties ─────────────────────────────────────────────────────
    @property
    def use_cloud_chroma(self) -> bool:
        return bool(
            self.CHROMA_API_KEY
            and self.CHROMA_TENANT
            and self.CHROMA_DATABASE
            and self.CHROMA_API_KEY.startswith("ck-")
        )

    @property
    def langsmith_enabled(self) -> bool:
        return bool(
            self.LANGSMITH_API_KEY
            and len(self.LANGSMITH_API_KEY) > 20
            and self.LANGSMITH_TRACING
        )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Strip surrounding quotes from values (e.g. LANGSMITH_PROJECT="foo")
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
