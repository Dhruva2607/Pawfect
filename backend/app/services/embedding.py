"""
Embedding generation service for PawFect pet vectors.
[FROM MARKDOWN] matches Step 1.2, Step 1.3, and Step 6.2 (768-dim vectors, exponential backoff).
"""

import time
import logging
from typing import List
from google import genai
from google.genai import types
from app.config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# [FROM MARKDOWN] 768 dimensions calibrated to Google embedding models
VECTOR_DIMENSION = 768

_client: genai.Client | None = None


def get_genai_client() -> genai.Client:
    """Return a singleton Google GenAI client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def generate_embedding(text: str, max_retries: int = 4) -> List[float]:
    """
    Generate a 768-dimensional embedding vector for a single text.
    Includes exponential backoff for rate limit handling [FROM MARKDOWN: Step 6.2].
    """
    client = get_genai_client()
    backoff = 1.0

    # Try gemini-embedding-001 with 768 dims first, then fallback to text-embedding-004
    candidate_models = ["models/gemini-embedding-001", "models/text-embedding-004"]

    for attempt in range(max_retries):
        for model_name in candidate_models:
            try:
                config = types.EmbedContentConfig(output_dimensionality=VECTOR_DIMENSION)
                resp = client.models.embed_content(
                    model=model_name,
                    contents=text,
                    config=config,
                )
                if resp.embeddings and len(resp.embeddings) > 0:
                    values = resp.embeddings[0].values
                    if len(values) == VECTOR_DIMENSION:
                        return values
                    return values[:VECTOR_DIMENSION]
            except Exception as e:
                # If model not found, try next candidate
                if "404" in str(e) or "NOT_FOUND" in str(e):
                    continue
                logger.warning("Embedding attempt %d failed on %s: %s", attempt + 1, model_name, e)

        time.sleep(backoff)
        backoff *= 2.0

    raise RuntimeError(f"Failed to generate embedding after {max_retries} attempts.")


def generate_batch_embeddings(texts: List[str], delay_between_calls: float = 0.3) -> List[List[float]]:
    """
    Generate embeddings for a list of texts with rate-limiting delay.
    """
    embeddings: List[List[float]] = []
    for idx, text in enumerate(texts):
        emb = generate_embedding(text)
        embeddings.append(emb)
        if idx < len(texts) - 1 and delay_between_calls > 0:
            time.sleep(delay_between_calls)
    return embeddings

