#!/bin/bash
# Install structured-output-ai from GitHub
set -e

pip install "git+https://github.com/FlossWare/structured-output-ai.git"

echo "structured-output-ai installed successfully"
echo "Verify: python3 -c 'import structured_output_ai; print(structured_output_ai.__version__)'"
