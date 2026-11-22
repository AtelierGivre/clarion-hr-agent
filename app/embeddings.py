import time

from google import genai
from google.genai import types

from app.config import EMBEDDING_DIM, EMBEDDING_MODEL, GEMINI_API_KEY

_client = None


def _get_client():
    """Create the GenAI client on first use so imports need no API key."""
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is required for embeddings")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    for attempt in range(4):
        try:
            response = _get_client().models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_DIM,
                ),
            )
            return [item.values for item in response.embeddings]
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")


def embed_documents(texts: list[str]) -> list[list[float]]:
    vectors: list[list[float]] = []
    for start in range(0, len(texts), 20):
        vectors.extend(_embed(texts[start : start + 20], "RETRIEVAL_DOCUMENT"))
    return vectors


def embed_query(text: str) -> list[float]:
    return _embed([text], "RETRIEVAL_QUERY")[0]


def to_pg_vector(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in values) + "]"
