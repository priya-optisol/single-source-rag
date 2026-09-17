"""LLM client factory. Any OpenAI-compatible endpoint works."""
import logging
from functools import lru_cache
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings

logger = logging.getLogger(__name__)
@lru_cache(maxsize=4)
def get_llm(temperature: float | None = None) -> ChatOpenAI:
    """Build (and cache) a chat client.
    Cached per temperature so the suggestions feature can use a warmer
    setting than the grounded-answer path without rebuilding clients.
    """
    return ChatOpenAI(
    model=settings.llm_model,
    api_key=settings.llm_api_key,
    base_url=settings.openai_base_url,
    temperature=settings.llm_temperature if temperature is None else temperature,
    timeout=60,
    max_retries=0, # we handle retries with tenacity below
    )
@retry(
stop=stop_after_attempt(3),
wait=wait_exponential(multiplier=1, min=2, max=10),
reraise=True,
)

def complete(prompt: str, temperature: float | None = None) -> str:
    """Single-turn completion with exponential backoff on transient failures."""
    response = get_llm(temperature).invoke(prompt)
    return response.content.strip()
