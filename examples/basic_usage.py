#!/usr/bin/env python3
"""Basic structured-output-ai usage: type-safe LLM responses."""
from __future__ import annotations

import asyncio
import json
from typing import Protocol, runtime_checkable

from structured_output_ai import (
    ChatMessage,
    ChatResponse,
    StructuredResponse,
    structured_output,
)

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
        "summary": {"type": "string"},
    },
}


@runtime_checkable
class LLMBackend(Protocol):
    async def chat(
        self, messages: list[ChatMessage], model: str, **kwargs
    ) -> ChatResponse: ...


class MockBackend:
    """Example backend that returns JSON. Replace with your real LLM backend."""

    async def chat(
        self, messages: list[ChatMessage], model: str, **kwargs
    ) -> ChatResponse:
        result = {
            "issues": [
                {"severity": "high", "description": "Missing input validation"},
                {"severity": "low", "description": "Variable name could be clearer"},
            ],
            "summary": "Found 2 issues in the code review",
        }
        return ChatResponse(
            content=json.dumps(result),
            model=model,
            usage={"prompt_tokens": 50, "completion_tokens": 80},
        )


async def main():
    backend = MockBackend()

    # Direct usage with StructuredResponse
    raw_response = await backend.chat(
        [ChatMessage(role="user", content="Review this code")],
        model="mock",
    )
    structured = StructuredResponse(
        parsed=json.loads(raw_response.content),
        raw=raw_response.content,
        schema=REVIEW_SCHEMA,
    )

    print(f"Parsed {len(structured.parsed['issues'])} issues:")
    for issue in structured.parsed["issues"]:
        print(f"  [{issue['severity']}] {issue['description']}")
    print(f"Summary: {structured.parsed['summary']}")


if __name__ == "__main__":
    asyncio.run(main())
