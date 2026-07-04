#!/usr/bin/env bash

set -euo pipefail
cd -- "$(dirname -- "$0")/.."

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

if ! python3 -c "import web_conductor, pytest" 2>/dev/null; then
    pip3 install -e .[test]
fi

python3 -m tests "$@"
