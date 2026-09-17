"""RAGAS scoring, run in the background and logged to JSONL."""
import json
import logging

from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger(__name__)

def _write(record: dict) -> None:
    """Append one JSON object as a line. Never raises into the caller."""
    try:
        settings.eval_log_path.parent.mkdir(parents=True, exist_ok=True)
        with settings.eval_log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        logger.exception("Could not write evaluation log.")

def evaluate_and_log(
document_id: str,
question: str,
answer: str,
contexts: list[str],
) -> None:
    """Score one Q/A/context triple and append the result.
    Runs inside a FastAPI BackgroundTask, so it must never raise --
    an exception here would be logged but is invisible to the user, and
    a failed evaluation must not look like a failed query.
    """
    base = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "document_id": document_id,
    "question": question,
    "answer_preview": answer[:200],
    "num_sources": len(contexts),
    }
    if not settings.enable_evaluation:
        return
    if not contexts or not answer.strip():
        _write({**base, "status": "error", "error": "empty answer or context",
            "metrics": {}})
        return

    try:
        from datasets import Dataset
        from langchain_huggingface import HuggingFaceEmbeddings
        from ragas import evaluate
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from ragas.metrics import answer_relevancy, context_precision, faithfulness
        from app.services.embeddings import get_embeddings
        from app.services.llm import get_llm
        dataset = Dataset.from_dict(
        {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts],
        }
        )
        result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
        llm=LangchainLLMWrapper(get_llm(temperature=0.0)),
        embeddings=LangchainEmbeddingsWrapper(get_embeddings()),
        raise_exceptions=False,
        )
        scores = result.to_pandas().iloc[0].to_dict()

        def num(key: str):
            value = scores.get(key)
            try:
                value = float(value)
            except (TypeError, ValueError):
                return None
            return None if value != value else round(value, 4) # NaN check
        _write(
            {
            **base,
            "status": "ok",
            "metrics": {
            "faithfulness": num("faithfulness"),
            "answer_relevancy": num("answer_relevancy"),
            "context_precision": num("context_precision"),
            },
            }
        )
        logger.info("Evaluation logged for document %s.", document_id)
    except Exception as exc: # noqa: BLE001
        logger.warning("RAGAS evaluation failed: %s", exc)
        _write({**base, "status": "error", "error": str(exc)[:300], "metrics": {}})
    
def read_evaluations(limit: int = 50) -> list[dict]:
    """Return the most recent evaluation records, newest first."""
    if not settings.eval_log_path.exists():
        return []
    try:
        lines = settings.eval_log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(records) >= limit:
            break
    return records