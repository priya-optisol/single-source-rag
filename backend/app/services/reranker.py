"""Cross-encoder re-ranking of FAISS candidates."""
import logging
from langchain_core.documents import Document
from app.config import settings
from app.services.embeddings import get_reranker
logger = logging.getLogger(__name__)

def rerank(
question: str,
candidates: list[Document],
top_n: int | None = None,
) -> list[tuple[Document, float, int]]:
    """Re-score candidates against the question and keep the best.
    Returns a list of (document, score, original_vector_rank), sorted by
    descending score. Keeping the original rank lets the UI show how much
    the re-ranker changed the ordering.
    """
    if not candidates:
        return []
    top_n = top_n or settings.rerank_top_n
    model = get_reranker()
    # The cross-encoder takes (query, passage) pairs and returns one logit each.
    pairs = [(question, doc.page_content) for doc in candidates]
    scores = model.predict(pairs)
    ranked = sorted(
    [(doc, float(score), i) for i, (doc, score) in enumerate(zip(candidates, scores))],
    key=lambda t: t[1],
    reverse=True,
    )
    if logger.isEnabledFor(logging.DEBUG):
        moved = sum(1 for new, (_, _, old) in enumerate(ranked[:top_n]) if new != old)
        logger.debug("Reranker reordered %d of the top %d.", moved, top_n)
    return ranked[:top_n]

def retrieve_and_rerank(
store,
question: str,
k: int | None = None,
top_n: int | None = None,
) -> list[tuple[Document, float, int]]:
    """The two-stage retrieval: wide vector recall, then precise re-ranking."""
    k = k or settings.retrieval_k
    candidates = store.similarity_search(question, k=k)
    logger.info("FAISS returned %d candidates.", len(candidates))
    return rerank(question, candidates, top_n=top_n)