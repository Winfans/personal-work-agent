"""Alibaba Bailian knowledge retrieval client."""

from dataclasses import dataclass
import json
import logging
from typing import Any

import httpx


logger = logging.getLogger("uvicorn.error")


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    content: str
    score: float | None = None
    source: str | None = None


class BailianRagService:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        index_id: str,
        top_k: int = 5,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._index_id = index_id
        self._top_k = top_k

    async def retrieve(self, query: str) -> list[RetrievedChunk]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self._base_url}/api/v1/indices/knowledge/search",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "agent_id": self._index_id,
                    "query": query,
                    "top_k": self._top_k,
                },
            )
            response.raise_for_status()

        body: dict[str, Any] = response.json()
        logger.info(
            "Bailian RAG response: %s",
            json.dumps(body, ensure_ascii=False, default=str),
        )
        container = body.get("data") or body.get("output") or body
        nodes = container.get("nodes", []) if isinstance(container, dict) else []
        chunks: list[RetrievedChunk] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            content = node.get("content") or node.get("text") or node.get("page_content")
            if not isinstance(content, str) or not content.strip():
                continue
            metadata = node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
            source = (
                node.get("source")
                or node.get("document_name")
                or metadata.get("source")
                or metadata.get("file_name")
            )
            score = node.get("score")
            chunks.append(
                RetrievedChunk(
                    content=content.strip(),
                    score=float(score) if isinstance(score, (int, float)) else None,
                    source=str(source) if source else None,
                )
            )
        return chunks
