"""Lazily-loaded, process-wide singletons for the local models."""
import logging
from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder
from app.config import settings

logger = logging.getLogger(__name__)
@lru_cache(maxsize=1)

def get_embeddings() -> HuggingFaceEmbeddings:
    """The bi-encoder used for both indexing and query embedding.
    Must be the same model on both sides -- vectors from different models
    live in different spaces and their distances are meaningless.
    """
    logger.info("Loading embedding model: %s", settings.embedding_model)
    return HuggingFaceEmbeddings(
    model_name=settings.embedding_model,
    model_kwargs={"device": "cpu"},
    # Normalising makes L2 distance monotonic with cosine similarity,
    # which is what all-MiniLM was trained for.
    encode_kwargs={"normalize_embeddings": True},
    )

@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """The cross-encoder used to re-score FAISS candidates."""
    logger.info("Loading reranker model: %s", settings.reranker_model)
    return CrossEncoder(settings.reranker_model, max_length=512, device="cpu")

def warm_up() -> None:
    """Force both models to load at startup rather than on first request."""
    get_embeddings().embed_query("warm up")
    get_reranker().predict([("warm up", "warm up")])
    logger.info("Models warmed up.")
