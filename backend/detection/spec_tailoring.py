"""Spec tailoring detector using pgvector cosine similarity."""
from __future__ import annotations

import hashlib
import math
import uuid
from typing import TYPE_CHECKING, Any

import numpy as np
import structlog

if TYPE_CHECKING:
    from models.tender import Tender
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

EMBEDDING_DIM = 1536
SIMILARITY_THRESHOLD = 0.92


def _text_to_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Hash-based deterministic pseudo-embedding for testing pgvector infrastructure.
    Groups tenders with similar words in similar regions of the vector space.
    """
    if not text:
        text = "untitled"

    # Tokenize into words
    words = text.lower().replace("-", " ").replace(",", " ").replace(".", " ").split()

    # Hash-trick: map each word to a position in the vector, accumulate
    vec = np.zeros(dim, dtype=np.float64)
    for word in words:
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        # Spread contribution across multiple dimensions
        for k in range(8):
            idx = (h >> (k * 4)) % dim
            sign = 1 if (h >> (k * 2)) & 1 else -1
            vec[idx] += sign * (1.0 / math.sqrt(len(words) + 1))

    # Normalize to unit length
    norm = np.linalg.norm(vec)
    if norm > 1e-10:
        vec = vec / norm

    return vec.tolist()


async def embed_tender_spec(tender: "Tender", api_key: str | None = None) -> list[float]:
    """Generate embedding for tender spec. Uses Claude API if key available, else hash-based."""
    text = tender.spec_text or tender.title or ""

    if api_key:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            # Use Claude to summarize and embed (via a text generation workaround)
            # In production, use a dedicated embedding API
            msg = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": f"Summarize this procurement spec in 30 words: {text[:500]}"
                }],
            )
            summary = msg.content[0].text
            return _text_to_embedding(summary)
        except Exception as exc:
            logger.warning("claude_embed_failed", error=str(exc))

    return _text_to_embedding(text)


async def find_similar_tenders(
    db: "AsyncSession",
    tender_id: uuid.UUID,
    embedding: list[float],
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find tenders with cosine similarity > threshold using pgvector."""
    from sqlalchemy import text

    embedding_str = "[" + ",".join(f"{v:.6f}" for v in embedding) + "]"
    query = text("""
        SELECT id, title, winner_vendor_id, ministry,
               1 - (spec_embedding <=> cast(:emb as vector)) AS similarity
        FROM tenders
        WHERE spec_embedding IS NOT NULL
          AND id != :tid
          AND 1 - (spec_embedding <=> cast(:emb as vector)) > :threshold
        ORDER BY similarity DESC
        LIMIT :lim
    """)
    result = await db.execute(query, {
        "emb": embedding_str,
        "tid": str(tender_id),
        "threshold": SIMILARITY_THRESHOLD,
        "lim": limit,
    })
    rows = result.fetchall()
    return [
        {
            "tender_id": str(row.id),
            "title": row.title,
            "winner_vendor_id": str(row.winner_vendor_id) if row.winner_vendor_id else None,
            "ministry": row.ministry,
            "similarity": round(float(row.similarity), 4),
        }
        for row in rows
    ]


async def detect_tailoring(
    db: "AsyncSession",
    tender: "Tender",
    api_key: str | None = None,
) -> dict | None:
    """Detect specification tailoring via vector similarity."""
    embedding = await embed_tender_spec(tender, api_key)

    # Store embedding
    from sqlalchemy import text, update
    embedding_str = "[" + ",".join(f"{v:.6f}" for v in embedding) + "]"
    await db.execute(
        text("UPDATE tenders SET spec_embedding = cast(:emb as vector) WHERE id = :tid"),
        {"emb": embedding_str, "tid": str(tender.id)},
    )

    similar = await find_similar_tenders(db, tender.id, embedding)
    if not similar:
        return None

    # Check if same vendor won similar-spec tenders
    same_vendor_hits = [
        s for s in similar
        if s["winner_vendor_id"] and str(s["winner_vendor_id"]) == str(tender.winner_vendor_id)
    ] if tender.winner_vendor_id else []

    if not same_vendor_hits:
        return None

    evidence = {
        "similar_tender_ids": [s["tender_id"] for s in same_vendor_hits],
        "similarity_scores": [s["similarity"] for s in same_vendor_hits],
        "common_winner": str(tender.winner_vendor_id),
        "spec_excerpt": (tender.spec_text or tender.title or "")[:200],
    }

    logger.info("anomaly_detected", type="spec_tailoring", tender_id=str(tender.id))
    return {
        "id": uuid.uuid4(),
        "tender_id": tender.id,
        "type": "spec_tailoring",
        "severity": "high",
        "evidence": evidence,
        "status": "open",
        "_risk_delta": 35,
    }
