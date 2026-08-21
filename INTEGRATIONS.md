# structured-output-ai Integrations

Install from GitHub:

```bash
pip install "git+https://github.com/FlossWare/structured-output-ai.git"
```

---

## Claude Code

### CLAUDE.md Snippet

```markdown
## Structured Output (structured-output-ai)

This project uses `structured-output-ai` for type-safe LLM responses.

- Structured output: `from structured_output_ai import structured_output, StructuredOutputBackend`
- Use `@structured_output` decorator to parse LLM responses into typed objects
- Supports JSON extraction, schema validation, and retry on parse failure
- Zero external dependencies (stdlib only)
```

### Hook Example

Create `.claude/hooks/post-tool-edit.py` to validate LLM-generated code:

```python
#!/usr/bin/env python3
"""Post-edit hook: validate structured output from LLM-generated code."""
from __future__ import annotations

import json
import sys

from structured_output_ai import StructuredResponse


def validate_output(text: str) -> bool:
    """Check if text contains valid structured output."""
    try:
        data = json.loads(text)
        return isinstance(data, (dict, list))
    except (json.JSONDecodeError, TypeError):
        return False


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else ""
    if file_path.endswith(".json"):
        with open(file_path) as f:
            content = f.read()
        if validate_output(content):
            print(f"[structured-output-ai] {file_path}: valid structured output")
        else:
            print(f"[structured-output-ai] {file_path}: WARNING - invalid JSON")
```

### Skill Example

Create `.claude/skills/extract-structured.md`:

```markdown
---
name: extract-structured
description: Extract structured data from LLM responses
---

Use structured-output-ai to extract typed data from model responses:

\```python
from structured_output_ai import structured_output

@structured_output(schema={"type": "object", "properties": {"answer": {"type": "string"}}})
async def get_answer(prompt: str, *, model: str = "default"):
    return await backend.chat([ChatMessage(role="user", content=prompt)], model=model)

# result = await get_answer("What is 2+2?")
# result.parsed  -> {"answer": "4"}
\```
```

---

## OpenAI Codex

### AGENTS.md Snippet

```markdown
## Structured Output

Use structured-output-ai for type-safe LLM responses:
- Install: `pip install "git+https://github.com/FlossWare/structured-output-ai.git"`
- Decorator: `@structured_output(schema={...})` wraps LLM calls to return parsed objects
- Backend: `StructuredOutputBackend` wraps any `LLMBackend` with automatic parsing
- Response: `StructuredResponse` contains `.parsed` (typed) and `.raw` (original)
```

### Tool Definition

```python
from structured_output_ai import structured_output, StructuredOutputBackend

# Decorator approach
@structured_output(schema={"type": "object", "properties": {"bugs": {"type": "array"}}})
async def find_bugs(prompt: str, *, model: str = "default"):
    return await backend.chat([ChatMessage(role="user", content=prompt)], model=model)

# Backend wrapper approach
structured_backend = StructuredOutputBackend(
    backend=my_backend,
    default_schema={"type": "object"},
)
response = await structured_backend.chat(messages, model="gpt-4o")
print(response.parsed)
```

---

## Cursor

### .cursorrules Snippet

```
When generating structured data from LLMs, use structured-output-ai:

- Import: from structured_output_ai import structured_output, StructuredOutputBackend, StructuredResponse
- Decorator: @structured_output(schema=json_schema) to parse responses automatically
- Backend wrapper: StructuredOutputBackend(backend, default_schema=schema)
- Response object: StructuredResponse with .parsed and .raw attributes
- Zero dependencies - stdlib only
- Install: pip install "git+https://github.com/FlossWare/structured-output-ai.git"
```

---

## Crush

### Configuration

```python
# crush.config.py
from structured_output_ai import structured_output, StructuredOutputBackend

async def extract_data(prompt: str, schema: dict, backend, model: str):
    """Extract structured data from LLM response."""
    structured = StructuredOutputBackend(backend=backend, default_schema=schema)
    response = await structured.chat(
        [{"role": "user", "content": prompt}], model=model
    )
    return response.parsed
```

---

## Generic Python Agent

### Basic Integration

```python
import asyncio
from structured_output_ai import structured_output, StructuredOutputBackend, StructuredResponse

# Schema for code review output
REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "line": {"type": "integer"},
                    "description": {"type": "string"},
                },
            },
        },
        "summary": {"type": "string"},
    },
}


@structured_output(schema=REVIEW_SCHEMA)
async def review_code(prompt: str, *, model: str = "default"):
    """Returns structured code review with typed issues."""
    return await backend.chat(
        [{"role": "user", "content": prompt}], model=model
    )


async def main():
    result = await review_code("Review this Python function for bugs")
    print(f"Found {len(result.parsed['issues'])} issues")
    for issue in result.parsed["issues"]:
        print(f"  [{issue['severity']}] Line {issue['line']}: {issue['description']}")
    print(f"Summary: {result.parsed['summary']}")

asyncio.run(main())
```

### Decorator Pattern

```python
from structured_output_ai import structured_output

SENTIMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
    },
}

@structured_output(schema=SENTIMENT_SCHEMA)
async def analyze_sentiment(text: str, *, model: str = "default"):
    prompt = f"Analyze the sentiment of this text: {text}"
    return await backend.chat([{"role": "user", "content": prompt}], model=model)
```

---

## Cross-Package Integration

### structured-output-ai + consensus-ai

Structured consensus: multiple models vote, result is parsed:

```python
from structured_output_ai import structured_output
from consensus_ai import with_consensus

@structured_output(schema=REVIEW_SCHEMA)
@with_consensus(strategy="majority_vote", models=["m1", "m2", "m3"])
async def consensus_review(prompt: str, *, model: str = "default"):
    return await backend.chat([{"role": "user", "content": prompt}], model=model)

# result.parsed is a dict matching REVIEW_SCHEMA
```

### structured-output-ai + evaluation-ai

Structured adversarial verification:

```python
from structured_output_ai import structured_output
from evaluation_ai import adversarial_verify

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_correct": {"type": "boolean"},
        "confidence": {"type": "number"},
        "evidence": {"type": "string"},
    },
}

@structured_output(schema=VERDICT_SCHEMA)
@adversarial_verify(backend=eval_backend, available_models=["m1", "m2"])
async def verified_analysis(prompt: str, *, model: str = "default"):
    return await backend.chat([{"role": "user", "content": prompt}], model=model)
```

### Recommended Decorator Stack Order

```python
@structured_output(schema=SCHEMA)     # outermost: parse final result
@track_execution(telemetry=t)         # track timing
@adversarial_verify(backend=b)        # verify output
@with_consensus(models=models)        # fan out to models
@with_retry(max_attempts=3)           # retry on failure
async def robust_structured(prompt, *, model="default"):
    ...
```
