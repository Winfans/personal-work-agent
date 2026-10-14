"""Jev-backed request routing."""

from dataclasses import dataclass
import json
import logging
from typing import Any, Literal

import httpx


logger = logging.getLogger("uvicorn.error")


RouteName = Literal["general_chat", "rag_chat"]


@dataclass(frozen=True, slots=True)
class RouteDecision:
    route: RouteName
    confidence: float | None = None
    model: str | None = None


class JevDecisionService:
    """Uses Jev only for typed routing decisions, never text generation."""

    def __init__(self, api_key: str, base_url: str, model: str, timeout: float) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def decide(self, message: str) -> RouteDecision:
        payload = {
            "model": self._model,
            "state": {"latest_user_message": message},
            "questions": {
                "route": {
                    "type": "choice",
                    "instructions": (
                        "Choose the single best processing route for the user's latest message."
                    ),
                    "criteria": {
                        "general_chat": (
                            "Casual conversation, writing, reasoning, or questions answerable from "
                            "general model knowledge without the private knowledge base."
                        ),
                        "rag_chat": (
                            "Questions that ask about private, internal, project-specific, uploaded, "
                            "or organization-specific facts that should be retrieved from the knowledge base."
                        ),
                    },
                }
            },
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/v1/systemone",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
            response.raise_for_status()

        data: dict[str, Any] = response.json()
        logger.info(
            "Jev response: %s",
            json.dumps(data, ensure_ascii=False, default=str),
        )
        answer = data.get("answers", {}).get("route", {})
        choice = answer.get("choice")
        if isinstance(choice, dict):
            choice = choice.get("value") or choice.get("choice")
        if choice not in {"general_chat", "rag_chat"}:
            raise RuntimeError(f"Jev returned an unsupported route: {choice!r}")

        confidence = answer.get("confidence")
        return RouteDecision(
            route=choice,
            confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
            model=data.get("model"),
        )
