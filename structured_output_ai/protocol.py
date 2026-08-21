"""Provider-agnostic LLM backend protocol.

Defines the ``LLMBackend`` protocol that any chat completion provider
must satisfy.  Uses :class:`typing.Protocol` for structural subtyping
-- implementors do not need to inherit from ``LLMBackend``.
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol, runtime_checkable

from structured_output_ai.types import ChatMessage, ChatResponse


@runtime_checkable
class LLMBackend(Protocol):
    """Provider-agnostic chat completion interface."""

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        """Send a chat completion request."""
        ...

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Stream content deltas."""
        ...
