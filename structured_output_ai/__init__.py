"""structured-output-ai -- Schema-validated JSON from LLMs with retries.

Zero required external dependencies.  ``jsonschema`` is used for full
JSON Schema validation when installed; a basic fallback validator is
provided otherwise.
"""

from __future__ import annotations

from structured_output_ai.protocol import LLMBackend
from structured_output_ai.structured_output import (
    StructuredOutputBackend,
    _extract_json,
    _validate_schema,
    structured_output,
)
from structured_output_ai.types import ChatMessage, ChatResponse, StructuredResponse

__all__ = [
    "ChatMessage",
    "ChatResponse",
    "LLMBackend",
    "StructuredOutputBackend",
    "StructuredResponse",
    "structured_output",
]

__version__ = "0.1"
