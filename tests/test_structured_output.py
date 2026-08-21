"""Tests for structured_output_ai."""

from __future__ import annotations

import json

import pytest

from structured_output_ai import (
    ChatMessage,
    ChatResponse,
    StructuredOutputBackend,
    StructuredResponse,
)
from structured_output_ai.structured_output import (
    _build_response,
    _extract_json,
    _normalize_parsed,
    _try_parse_json,
    _validate_schema,
    structured_output,
)


# -- Fake backend for testing -----------------------------------------------


class FakeBackend:
    """A fake LLMBackend that returns preconfigured responses."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return ChatResponse(content=self._responses[idx])

    async def chat_stream(self, messages, **kwargs):
        yield "chunk"


# -- Unit tests for helper functions ----------------------------------------


class TestExtractJson:
    def test_plain_json(self) -> None:
        assert _extract_json('{"a": 1}') == '{"a": 1}'

    def test_markdown_fence(self) -> None:
        text = '```json\n{"a": 1}\n```'
        assert _extract_json(text) == '{"a": 1}'

    def test_markdown_fence_no_lang(self) -> None:
        text = '```\n[1, 2, 3]\n```'
        assert _extract_json(text) == "[1, 2, 3]"

    def test_whitespace_stripping(self) -> None:
        assert _extract_json("  \n  {}\n  ") == "{}"


class TestValidateSchema:
    def test_valid_object(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        ok, err = _validate_schema({"name": "Alice"}, schema)
        assert ok is True
        assert err == ""

    def test_missing_required_key(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        ok, err = _validate_schema({}, schema)
        assert ok is False
        assert "name" in err

    def test_wrong_type_object(self) -> None:
        schema = {"type": "object"}
        ok, err = _validate_schema([1, 2], schema)
        assert ok is False
        assert "object" in err.lower()

    def test_wrong_type_array(self) -> None:
        schema = {"type": "array"}
        ok, err = _validate_schema({"a": 1}, schema)
        assert ok is False
        assert "array" in err.lower()

    def test_additional_properties_false(self) -> None:
        schema = {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "additionalProperties": False,
        }
        ok, err = _validate_schema({"x": 1, "y": 2}, schema)
        assert ok is False
        assert "y" in err

    def test_no_schema_type_passthrough(self) -> None:
        """Non-dict parsed values with no type constraint pass."""
        ok, err = _validate_schema(42, {})
        assert ok is True


class TestTryParseJson:
    def test_valid_json(self) -> None:
        parsed, err = _try_parse_json('{"key": "value"}')
        assert parsed == {"key": "value"}
        assert err is None

    def test_invalid_json(self) -> None:
        parsed, err = _try_parse_json("not json at all")
        assert parsed is None
        assert err is not None


class TestNormalizeParsed:
    def test_dict_passthrough(self) -> None:
        d = {"a": 1}
        assert _normalize_parsed(d) is d

    def test_non_dict_passthrough(self) -> None:
        assert _normalize_parsed([1, 2]) == [1, 2]
        assert _normalize_parsed(42) == 42


class TestBuildResponse:
    def test_fields(self) -> None:
        resp = _build_response(
            "raw", {"k": "v"}, schema_valid=True, retries_used=1
        )
        assert isinstance(resp, StructuredResponse)
        assert resp.content == "raw"
        assert resp.raw_text == "raw"
        assert resp.parsed == {"k": "v"}
        assert resp.schema_valid is True
        assert resp.retries_used == 1


# -- Integration tests for StructuredOutputBackend --------------------------


class TestStructuredOutputBackend:
    @pytest.mark.asyncio
    async def test_valid_json_no_schema(self) -> None:
        backend = FakeBackend(['{"greeting": "hello"}'])
        sob = StructuredOutputBackend(backend, default_model="test-model")
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="say hi")],
            response_format="json",
        )
        assert result.schema_valid is True
        assert result.parsed == {"greeting": "hello"}
        assert result.retries_used == 0

    @pytest.mark.asyncio
    async def test_valid_json_with_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        backend = FakeBackend(['{"name": "Bob"}'])
        sob = StructuredOutputBackend(backend)
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="generate")],
            schema=schema,
            response_format="json",
        )
        assert result.schema_valid is True
        assert result.parsed == {"name": "Bob"}

    @pytest.mark.asyncio
    async def test_retry_on_invalid_json(self) -> None:
        backend = FakeBackend(["not json", '{"ok": true}'])
        sob = StructuredOutputBackend(backend)
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="go")],
            response_format="json",
        )
        assert result.schema_valid is True
        assert result.parsed == {"ok": True}
        assert result.retries_used == 1
        assert backend.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_schema_failure(self) -> None:
        schema = {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "required": ["x"],
        }
        backend = FakeBackend(['{"y": 1}', '{"x": 42}'])
        sob = StructuredOutputBackend(backend)
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="go")],
            schema=schema,
            response_format="json",
        )
        assert result.schema_valid is True
        assert result.parsed == {"x": 42}
        assert result.retries_used == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries_invalid_json(self) -> None:
        backend = FakeBackend(["bad"] * 5)
        sob = StructuredOutputBackend(backend)
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="go")],
            response_format="json",
            max_retries=2,
        )
        assert result.schema_valid is False
        assert result.parsed is None
        assert result.retries_used == 2
        assert backend.call_count == 3

    @pytest.mark.asyncio
    async def test_exhausted_retries_schema_failure(self) -> None:
        schema = {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "required": ["x"],
        }
        backend = FakeBackend(['{"y": 1}'] * 5)
        sob = StructuredOutputBackend(backend)
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="go")],
            schema=schema,
            response_format="json",
            max_retries=2,
        )
        assert result.schema_valid is False
        assert result.retries_used == 2

    @pytest.mark.asyncio
    async def test_array_response_normalized(self) -> None:
        backend = FakeBackend(["[1, 2, 3]"])
        sob = StructuredOutputBackend(backend)
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="list")],
            response_format="json",
        )
        assert result.schema_valid is True
        assert result.parsed == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_markdown_fenced_json(self) -> None:
        backend = FakeBackend(['```json\n{"status": "ok"}\n```'])
        sob = StructuredOutputBackend(backend)
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="go")],
            response_format="json",
        )
        assert result.schema_valid is True
        assert result.parsed == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_text_format_still_parses(self) -> None:
        """response_format='text' still works if the model returns JSON."""
        backend = FakeBackend(['{"a": 1}'])
        sob = StructuredOutputBackend(backend)
        result = await sob.chat_structured(
            [ChatMessage(role="user", content="go")],
            response_format="text",
        )
        assert result.schema_valid is True
        assert result.parsed == {"a": 1}

    @pytest.mark.asyncio
    async def test_model_and_temperature_kwargs(self) -> None:
        """Verify model and temperature are forwarded to the backend."""
        calls: list[dict] = []

        class TrackingBackend:
            async def chat(self, messages, *, model=None, temperature=0.7, max_tokens=None):
                calls.append({"model": model, "temperature": temperature})
                return ChatResponse(content='{"ok": true}')

        sob = StructuredOutputBackend(TrackingBackend())
        await sob.chat_structured(
            [ChatMessage(role="user", content="go")],
            response_format="json",
            model="custom-model",
            temperature=0.2,
        )
        assert calls[0]["model"] == "custom-model"
        assert calls[0]["temperature"] == 0.2


# -- Tests for @structured_output decorator (ADR-0006) ----------------------


class TestStructuredOutputDecorator:
    @pytest.mark.asyncio
    async def test_valid_json_no_schema(self) -> None:
        """Decorator with no schema accepts any valid JSON."""
        call_count = 0

        @structured_output()
        async def my_llm(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            return ChatResponse(content='{"greeting": "hi"}')

        result = await my_llm([ChatMessage(role="user", content="hello")])
        assert result.schema_valid is True
        assert result.parsed == {"greeting": "hi"}
        assert result.retries_used == 0
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_valid_json_with_schema(self) -> None:
        """Decorator validates against provided schema."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }

        @structured_output(schema=schema)
        async def my_llm(messages, **kwargs):
            return ChatResponse(content='{"name": "Alice"}')

        result = await my_llm([ChatMessage(role="user", content="go")])
        assert result.schema_valid is True
        assert result.parsed == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_retry_on_invalid_json(self) -> None:
        """Decorator retries when model returns non-JSON."""
        responses = iter(["not json", '{"ok": true}'])

        @structured_output()
        async def my_llm(messages, **kwargs):
            return ChatResponse(content=next(responses))

        result = await my_llm([ChatMessage(role="user", content="go")])
        assert result.schema_valid is True
        assert result.parsed == {"ok": True}
        assert result.retries_used == 1

    @pytest.mark.asyncio
    async def test_retry_on_schema_mismatch(self) -> None:
        """Decorator retries when JSON does not match schema."""
        schema = {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "required": ["x"],
        }
        responses = iter(['{"y": 1}', '{"x": 99}'])

        @structured_output(schema=schema, max_retries=3)
        async def my_llm(messages, **kwargs):
            return ChatResponse(content=next(responses))

        result = await my_llm([ChatMessage(role="user", content="go")])
        assert result.schema_valid is True
        assert result.parsed == {"x": 99}
        assert result.retries_used == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries(self) -> None:
        """Decorator returns schema_valid=False after max_retries."""
        schema = {
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "required": ["x"],
        }

        @structured_output(schema=schema, max_retries=2)
        async def my_llm(messages, **kwargs):
            return ChatResponse(content='{"y": 1}')

        result = await my_llm([ChatMessage(role="user", content="go")])
        assert result.schema_valid is False
        assert result.retries_used == 2

    @pytest.mark.asyncio
    async def test_preserves_function_name(self) -> None:
        """Decorator preserves the wrapped function's name (functools.wraps)."""

        @structured_output()
        async def my_custom_llm_call(messages, **kwargs):
            return ChatResponse(content='{"a": 1}')

        assert my_custom_llm_call.__name__ == "my_custom_llm_call"

    @pytest.mark.asyncio
    async def test_kwargs_forwarded(self) -> None:
        """Decorator forwards keyword arguments to the wrapped function."""
        captured: dict = {}

        @structured_output()
        async def my_llm(messages, *, model=None, temperature=0.7, **kwargs):
            captured["model"] = model
            captured["temperature"] = temperature
            return ChatResponse(content='{"ok": true}')

        await my_llm(
            [ChatMessage(role="user", content="go")],
            model="gpt-4o",
            temperature=0.1,
        )
        assert captured["model"] == "gpt-4o"
        assert captured["temperature"] == 0.1

    @pytest.mark.asyncio
    async def test_appends_retry_messages(self) -> None:
        """Decorator appends corrective messages on retry."""
        all_messages: list[list] = []
        responses = iter(["not json", '{"ok": true}'])

        @structured_output()
        async def my_llm(messages, **kwargs):
            all_messages.append(list(messages))
            return ChatResponse(content=next(responses))

        await my_llm([ChatMessage(role="user", content="go")])
        # First call: original message only
        assert len(all_messages[0]) == 1
        # Second call: original + assistant reply + user fix prompt
        assert len(all_messages[1]) == 3
        assert all_messages[1][1].role == "assistant"
        assert all_messages[1][2].role == "user"
