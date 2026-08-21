#!/bin/bash
# Add structured-output-ai integration to your CLAUDE.md
set -e

CLAUDE_MD="${CLAUDE_MD:-./CLAUDE.md}"

if [ ! -f "$CLAUDE_MD" ]; then
    echo "Creating $CLAUDE_MD"
    touch "$CLAUDE_MD"
fi

cat >> "$CLAUDE_MD" << 'EOF'

## Structured Output (structured-output-ai)

This project uses [structured-output-ai](https://github.com/FlossWare/structured-output-ai) for type-safe LLM responses.

**Install:** `pip install "git+https://github.com/FlossWare/structured-output-ai.git"`

**Key imports:**
```python
from structured_output_ai import structured_output, StructuredOutputBackend, StructuredResponse
```

**Usage patterns:**
- Decorator: `@structured_output(schema={...})` to auto-parse LLM responses
- Backend wrapper: `StructuredOutputBackend(backend, default_schema=schema)`
- Response: `StructuredResponse` with `.parsed` (typed dict) and `.raw` (original)
- Zero external dependencies (stdlib only)
EOF

echo "Added structured-output-ai integration to $CLAUDE_MD"
