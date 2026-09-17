"""Application configuration, loaded from environment / .env."""
from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent # -> backend/

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore")
    # ---- LLM ----
    llm_api_key: str = Field(..., description="API key for the OpenAI-compatible endpoint")
    openai_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "google/gemini-2.0-flash-001"
    llm_temperature: float = 0.1
    # ---- Local models ----
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ---- Retrieval ----
    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_k: int = 20 # candidates from FAISS
    rerank_top_n: int = 5 # survivors after cross-encoder

    # ---- Paths (relative to backend/) ----
    faiss_index_path: Path = BASE_DIR / "data" / "faiss_index"
    upload_path: Path = BASE_DIR / "data" / "uploads"
    eval_log_path: Path = BASE_DIR / "logs" / "ragas_eval.jsonl"

    # ---- Limits ----
    max_upload_mb: int = 50

    # ---- Server ----
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    log_level: str = "INFO"
    enable_evaluation: bool = True
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024
    def ensure_dirs(self) -> None:
      """ Create the directories the app writes to. """
      self.faiss_index_path.mkdir(parents=True, exist_ok=True)
      self.upload_path.mkdir(parents=True, exist_ok=True)
      self.eval_log_path.parent.mkdir(parents=True, exist_ok=True)

@lru_cache
def get_settings() -> Settings:
    """Cached so the .env is parsed exactly once per process."""
    return Settings()
settings = get_settings()
