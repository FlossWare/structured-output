"""Core data types for structured-output-ai.

Plain dataclasses with no imports outside the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """A single message in an LLM chat conversation."""

    role: str
    content: str


@dataclass
class ChatResponse:
    """Response from an LLM chat completion request."""

    content: str
    model: str = ""
    provider: str = ""
    usage: dict = field(default_factory=dict)


@dataclass
class StructuredResponse:
    """Response from a structured-output chat completion."""

    content: str
    parsed: Any | None = None
    schema_valid: bool = False
    raw_text: str = ""
    retries_used: int = 0
