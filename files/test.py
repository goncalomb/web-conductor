#!/usr/bin/env -S pipx run --path

# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pytest",
#   "pytest-cov",
#   "syrupy",
#   "pyyaml",
#   "pydantic",
# ]
# ///

import sys

import pytest

DEFAULT_ARGS = [
    '--cov=src',
    '--cov-report=term-missing:skip-covered',
    '--cov-report=html',
]

if __name__ == '__main__':
    sys.exit(pytest.main(sys.argv[1:] or DEFAULT_ARGS))
