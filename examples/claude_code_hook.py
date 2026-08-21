#!/usr/bin/env python3
"""Claude Code hook: validate JSON files against schemas.

Usage as a pre-commit hook in .claude/hooks/pre-commit.py:
    python3 examples/claude_code_hook.py "$FILE_PATH"
"""
from __future__ import annotations

import json
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: claude_code_hook.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not file_path.endswith(".json"):
        sys.exit(0)

    try:
        with open(file_path) as f:
            data = json.load(f)
    except (FileNotFoundError, IsADirectoryError):
        sys.exit(0)
    except json.JSONDecodeError as e:
        print(f"[structured-output-ai] INVALID JSON in {file_path}: {e}")
        sys.exit(1)

    if isinstance(data, dict):
        print(f"[structured-output-ai] {file_path}: valid object with {len(data)} keys")
    elif isinstance(data, list):
        print(f"[structured-output-ai] {file_path}: valid array with {len(data)} items")
    else:
        print(f"[structured-output-ai] {file_path}: valid JSON ({type(data).__name__})")


if __name__ == "__main__":
    main()
