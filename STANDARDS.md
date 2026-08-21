# FlossWare Engineering Standards Compliance

This package adheres to the
[FlossWare Engineering Standards](https://github.com/FlossWare/engineering-standards).

## Applicable ADRs

### ADR-0001: Explicit Opt-In

Schema validation and retry behavior never activate automatically.
Users must explicitly wrap their LLM backend via `StructuredOutputBackend`
or apply the `@structured_output` decorator. No global state, no
monkey-patching, no implicit middleware.

- `StructuredOutputBackend(backend)` -- explicit wrapper construction
- `@structured_output(schema=...)` -- explicit decorator application

### ADR-0006: Cross-Cutting Decorators

The `@structured_output` decorator provides a composable, cross-cutting
concern (JSON schema validation with retries) that can be applied to any
async LLM call without modifying the function body.

```python
@structured_output(schema={"type": "object", "required": ["name"]})
async def get_profile(messages, *, model=None, temperature=0.7, **kw):
    return ChatResponse(content=await call_llm(messages))
```

### ADR-0008: Free-First

Zero required external dependencies. The package uses only the Python
standard library. The optional `jsonschema` package enables full JSON
Schema validation when installed; a built-in fallback validator handles
basic type and key checks otherwise.

### ADR-0009: Core Principles

- **Modular:** Each concern (types, protocol, structured output) lives in
  its own module.
- **Composable:** `StructuredOutputBackend` wraps any `LLMBackend`;
  `@structured_output` wraps any async function. Both compose freely
  with other middleware.
- **Contracts over implementations:** The `LLMBackend` protocol defines
  the contract via `typing.Protocol` (structural subtyping). No base
  class inheritance required.

### ADR-0017: Agent-Neutral

The package works with any agent runtime. It depends only on Python's
`asyncio` and imposes no framework, event loop, or orchestration
requirements. Any async callable returning `ChatResponse` is compatible.

### ADR-0020: Capability-Protocol Separation

Structured output is a capability layered on top of a transport-agnostic
`LLMBackend` protocol. The capability (schema validation, retry logic)
is fully independent of how the underlying LLM is accessed -- HTTP,
gRPC, in-process, or mock.
