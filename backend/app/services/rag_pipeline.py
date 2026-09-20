"""End-to-end orchestration of a single query."""
import logging
import time

from langchain_core.documents import Document

from app.config import settings
from app.models import SourceChunk
from app.services.document_processor import load_index
from app.services.llm import complete
from app.services.reranker import retrieve_and_rerank

logger = logging.getLogger(__name__)
# Below this cross-encoder score, we treat the document as simply not
# containing the answer, and skip the LLM call entirely.
GROUNDING_THRESHOLD = -3.0

ANSWER_PROMPT = """You are a precise assistant answering questions about a \
single document. You have been given numbered excerpts from that document.
Rules you must follow:
1. Answer ONLY from the excerpts below. Do not use outside knowledge.
2. Cite the excerpt numbers you used, like [1] or [2][4], inline.
3. If the excerpts do not contain the answer, say exactly:
"I could not find this in the document."
Then briefly state what the document does cover on the nearest topic.
4. Do not speculate, infer beyond the text, or fill gaps with plausible detail.
5. Be concise. Two to five sentences unless the question needs more.
--- DOCUMENT EXCERPTS ---
{context}
--- END EXCERPTS ---
Question: {question}
Answer:"""
NO_CONTEXT_MESSAGE = (
"I could not find this in the document. Try rephrasing your question, "
"or ask about a topic the document actually covers."
)
def _format_context(ranked: list[tuple[Document, float, int]]) -> str:
    """Render the surviving chunks as a numbered, page-labelled block."""
    parts = []
    for n, (doc, _score, _rank) in enumerate(ranked, start=1):
        page = doc.metadata.get("page")
        label = f"[{n}]" + (f" (page {page})" if page else "")
        parts.append(f"{label}\n{doc.page_content.strip()}")
    return "\n\n".join(parts)

def answer_question(document_id: str, question: str) -> dict:
    """Retrieve, re-rank, generate. Returns everything the API needs."""
    started = time.perf_counter()
    store = load_index(document_id)
    ranked = retrieve_and_rerank(store, question)
    sources = [
    SourceChunk(
    text=doc.page_content.strip(),
    page=doc.metadata.get("page"),
    chunk_index=doc.metadata.get("chunk_index", -1),
    rerank_score=round(score, 4),
    vector_rank=rank,
    )
    for doc, score, rank in ranked
    ]
    # Grounding gate: if even the best chunk is weak, do not call the LLM.
    best = ranked[0][1] if ranked else float("-inf")
    if best < GROUNDING_THRESHOLD:
        logger.info("Below grounding threshold (best=%.2f); skipping LLM.", best)
        return {
        "answer": NO_CONTEXT_MESSAGE,
        "sources": sources,
        "contexts": [s.text for s in sources],
        "grounded": False,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        }
    prompt = ANSWER_PROMPT.format(
        context=_format_context(ranked),
        question=question.strip(),
        )
    answer = complete(prompt)
    return {
    "answer": answer,
    "sources": sources,
    "contexts": [s.text for s in sources], # RAGAS wants plain strings
    "grounded": True,
    "latency_ms": int((time.perf_counter() - started) * 1000),
    }
# --------------------------------------------------------------------------
# Suggestions and topics -- both sample the document rather than retrieve.
# --------------------------------------------------------------------------
SUGGESTIONS_PROMPT = """Below are excerpts from a document. Propose {n} \
specific questions that this document can definitively answer.
Requirements:
- Each question must be answerable from the text shown, not from general knowledge.
- Be specific. "What are the three phases described in section 2?" not "What is this about?"
- Vary the type: some factual, some comparative, some about process or reasoning.
- Return ONLY a JSON array of strings. No markdown fences, no commentary.
--- EXCERPTS ---
{context}
--- END ---
JSON array:"""
TOPICS_PROMPT = """Below are excerpts from a document. Identify its {n} main \
topics.
Return ONLY a JSON array of objects, each with exactly two keys:
"title" -- 2 to 5 words
"summary" -- one sentence, under 20 words
No markdown fences, no commentary.
--- EXCERPTS ---
{context}
--- END ---
JSON array:"""

def _sample_context(document_id: str, max_chars: int = 8000) -> str:
    """Take an even spread of chunks across the document.
    Sampling evenly matters: the first N chunks of a report are a title page
    and a table of contents, which produce useless topics.
    Keep the context small enough for low-credit OpenRouter accounts.
    """
    from app.services.document_processor import get_all_chunks
    chunks = get_all_chunks(document_id)
    if not chunks:
        return ""
    step = max(1, len(chunks) // 16)
    sampled = chunks[::step][:16]
    out, total = [], 0
    for c in sampled:
        text = c.page_content.strip()
        if total + len(text) > max_chars:
            break
        out.append(text)
        total += len(text)
    return "\n\n---\n\n".join(out)

def _parse_json_array(raw: str) -> list:
    """LLMs wrap JSON in markdown fences no matter what you tell them."""
    import json
    import re
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        logger.warning("Could not parse LLM JSON output.")
    return []

def generate_suggestions(document_id: str, n: int = 5) -> list[str]:
    context = _sample_context(document_id)
    if not context:
        return []
    raw = complete(SUGGESTIONS_PROMPT.format(n=n, context=context), temperature=0.5)
    return [str(q) for q in _parse_json_array(raw) if isinstance(q, str)][:n]

def extract_topics(document_id: str, n: int = 6) -> list[dict]:
    context = _sample_context(document_id)
    if not context:
        return []
    raw = complete(TOPICS_PROMPT.format(n=n, context=context), temperature=0.3)
    topics = []
    for item in _parse_json_array(raw):
        if isinstance(item, dict) and "title" in item:
            topics.append(
            {"title": str(item["title"]), "summary": str(item.get("summary", ""))}
            )
    return topics[:n]