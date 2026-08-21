# structured-output-ai

Schema-validated JSON output from LLMs with automatic retries.

Wraps any LLM backend to guarantee structured JSON responses that conform to
a provided JSON Schema. When a model returns malformed or non-conforming JSON,
the library automatically retries with corrective prompts -- up to a
configurable number of attempts.

**Zero required external dependencies.** The optional `jsonschema` package
enables full JSON Schema validation; a built-in fallback handles basic
type and key checks when it is not installed.

## Installation

```bash
pip install structured-output-ai

# For full JSON Schema validation:
pip install structured-output-ai[jsonschema]
```

## Quickstart

```python
import asyncio
from structured_output_ai import (
    ChatMessage,
    ChatResponse,
    StructuredOutputBackend,
)

# 1. Implement the LLMBackend protocol (or use an existing one)
class MyBackend:
    async def chat(self, messages, *, model=None, temperature=0.7, max_tokens=None):
        # Call your LLM provider here
        return ChatResponse(content='{"name": "Alice", "age": 30}')

# 2. Define a JSON Schema for the expected output
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
}

# 3. Use StructuredOutputBackend to get validated responses
async def main():
    backend = StructuredOutputBackend(MyBackend(), default_model="gpt-4o")
    response = await backend.chat_structured(
        [ChatMessage(role="user", content="Generate a person profile")],
        schema=schema,
        response_format="json",
    )
    print(response.parsed)        # {'name': 'Alice', 'age': 30}
    print(response.schema_valid)  # True
    print(response.retries_used)  # 0

asyncio.run(main())
```

## API Overview

### Data Types

| Class | Description |
|-------|-------------|
| `ChatMessage` | A chat message with `role` and `content` fields |
| `ChatResponse` | LLM response with `content`, `model`, `provider`, and `usage` |
| `StructuredResponse` | Structured result with `parsed` dict, `schema_valid` flag, and `retries_used` count |

### Protocol

`LLMBackend` -- A `typing.Protocol` that any chat completion provider can
satisfy via structural subtyping. Requires an async `chat()` method.

### StructuredOutputBackend

The main entry point. Wraps any `LLMBackend` and exposes:

- **`chat_structured(messages, *, schema, response_format, max_retries, **kwargs)`** --
  Sends a chat completion request, parses the JSON response, validates it
  against the schema, and retries with corrective prompts on failure.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | `list[ChatMessage]` | required | Conversation messages |
| `schema` | `dict \| None` | `None` | JSON Schema to validate against |
| `response_format` | `str` | `"text"` | Set to `"json"` to prepend a JSON instruction |
| `max_retries` | `int` | `3` | Maximum retry attempts for invalid output |
| `model` | `str \| None` | instance default | Model to use |
| `temperature` | `float` | `0.7` | Sampling temperature |

### `@structured_output` Decorator

A convenience decorator (per ADR-0006) that wraps any async LLM call with
JSON schema validation and automatic retries:

```python
from structured_output_ai import ChatResponse, structured_output

@structured_output(schema={"type": "object", "required": ["name"]}, max_retries=3)
async def get_profile(messages, *, model=None, temperature=0.7, **kw):
    # Call your LLM however you like
    return ChatResponse(content=await call_my_llm(messages, model=model))

result = await get_profile([ChatMessage(role="user", content="Generate a profile")])
print(result.parsed)        # {'name': '...'}
print(result.schema_valid)  # True
```

## FlossWare Engineering Standards

This package complies with the
[FlossWare Engineering Standards](https://github.com/FlossWare/engineering-standards).
See [STANDARDS.md](STANDARDS.md) for full details.

| ADR | Principle | How It Applies |
|-----|-----------|----------------|
| ADR-0001 | Explicit Opt-In | Validation only activates when you wrap a backend or apply the decorator |
| ADR-0006 | Cross-Cutting Decorators | `@structured_output` decorator for composable schema enforcement |
| ADR-0008 | Free-First | Zero required dependencies; `jsonschema` is optional |
| ADR-0009 | Core Principles | Modular, composable, contracts over implementations |
| ADR-0017 | Agent-Neutral | Works with any agent runtime or async framework |
| ADR-0020 | Capability-Protocol Separation | Structured output is transport-independent |

## License

MIT
