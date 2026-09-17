"""PDF ingestion: parse, chunk, embed, persist."""

import logging
import shutil
import uuid
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings
from app.services.embeddings import get_embeddings
logger = logging.getLogger(__name__)

class DocumentProcessingError(Exception):
    """Raised when a PDF cannot be turned into a usable index."""

def _index_dir(document_id: str) -> Path:
    return settings.faiss_index_path / document_id

def validate_document_id(document_id: str) -> str:
    """Reject anything that is not a well-formed UUID.
    This value becomes part of a filesystem path, so it is a path-traversal
    vector if taken on trust."""
    try:
        return str(uuid.UUID(document_id))
    except (ValueError, AttributeError, TypeError) as exc:
        raise DocumentProcessingError("Invalid document_id.") from exc

def load_pdf(path: Path) -> list[Document]:
    """Extract text from a PDF, one Document per page."""
    loader = PyPDFLoader(str(path))
    pages = loader.load()
    non_empty = [p for p in pages if p.page_content and p.page_content.strip()]
    if not non_empty:
        raise DocumentProcessingError(
        "No extractable text found. This PDF is probably a scan -- "
        "run it through OCR (e.g. ocrmypdf) and upload the result."
        )
    logger.info("Extracted text from %d/%d pages.", len(non_empty), len(pages))
    return non_empty

def chunk_documents(pages: list[Document], document_id: str) -> list[Document]:
    """Split pages into overlapping chunks and attach metadata."""
    splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    # Tried in order: paragraph, line, sentence, clause, word, character.
    # Earlier separators preserve more semantic structure.
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
    )
    chunks = splitter.split_documents(pages)
    for i, chunk in enumerate(chunks):
        # PyPDFLoader pages are 0-indexed; humans count from 1.
        raw_page = chunk.metadata.get("page")
        chunk.metadata.update(
        {
        "document_id": document_id,
        "chunk_index": i,
        "page": (raw_page + 1) if isinstance(raw_page, int) else None,
        }
        )
    logger.info("Split into %d chunks.", len(chunks))
    return chunks

def build_index(chunks: list[Document], document_id: str) -> None:
    """Embed every chunk and persist the FAISS index to disk."""
    if not chunks:
        raise DocumentProcessingError("Nothing to index.")
    store = FAISS.from_documents(chunks, get_embeddings())
    target = _index_dir(document_id)
    target.mkdir(parents=True, exist_ok=True)
    store.save_local(str(target))
    logger.info("Saved FAISS index to %s", target)

def load_index(document_id: str) -> FAISS:
    """Load a persisted index. Raises if the document is unknown."""
    document_id = validate_document_id(document_id)
    target = _index_dir(document_id)
    if not target.exists():
        raise DocumentProcessingError(f"Unknown document_id: {document_id}")
    return FAISS.load_local(
    str(target),
    get_embeddings(),
    # Safe here: we wrote these files ourselves, in this container.
    # Never set this on an index from an untrusted source -- it pickles.
    allow_dangerous_deserialization=True,
    )

def ingest_pdf(file_bytes: bytes, filename: str) -> dict:
    """Full upload pipeline. Returns summary stats for the API response."""
    document_id = str(uuid.uuid4())
    saved_path = settings.upload_path / f"{document_id}.pdf"
    try:
        saved_path.write_bytes(file_bytes)
        pages = load_pdf(saved_path)
        chunks = chunk_documents(pages, document_id)
        build_index(chunks, document_id)
    except DocumentProcessingError:
        _cleanup(document_id, saved_path)
        raise
    except Exception as exc: # noqa: BLE001
        _cleanup(document_id, saved_path)
        logger.exception("Ingestion failed for %s", filename)
        raise DocumentProcessingError(f"Failed to process PDF: {exc}") from exc
    return {
        "document_id": document_id,
        "filename": filename,
        "pages": len({c.metadata.get("page") for c in chunks}),
        "chunks": len(chunks),
        }

def _cleanup(document_id: str, saved_path: Path) -> None:
    """Remove partial artefacts so a failed upload leaves no orphans."""
    saved_path.unlink(missing_ok=True)
    shutil.rmtree(_index_dir(document_id), ignore_errors=True)

def get_all_chunks(document_id: str, limit: int | None = None) -> list[Document]:
    """Return the stored chunks, in original order.
    Used by the suggestions and topics features, which need a sample of the
    document rather than a retrieval result.
    """
    store = load_index(document_id)
    docs = list(store.docstore._dict.values()) # noqa: SLF001
    docs.sort(key=lambda d: d.metadata.get("chunk_index", 0))
    return docs[:limit] if limit else docs
