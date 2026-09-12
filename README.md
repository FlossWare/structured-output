# structured-output

Reusable structured-output capability for FlossWare.

This repository validates model responses against schemas and can retry malformed or non-conforming output.

## Architectural boundary

Structured output is a **result contract**, not a model backend or orchestration layer.

- `model-gateway` owns provider/model invocation.
- `structured-output` validates and normalizes the returned representation.
- `evaluation` decides whether the resulting artifact satisfies an Intent.
- Loom owns Workers, Arbiters, execution, retries/replanning at the task level, and orchestration.

```text
Worker -> model-gateway -> structured-output -> typed result
                              |
                              v
                         validation evidence
```

Provider-specific structured-output mechanisms should be adapted by `model-gateway`; this repository provides reusable schema/validation behavior.

## Status

Active supporting capability. Keep the package transport-independent and free of agent-runtime assumptions.

## License

MIT
