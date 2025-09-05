#!/usr/bin/env bash
set -euo pipefail

# Simple demo runner for Interview Prep Agent
# Usage: scripts/demo.sh <company_domain> <user_email> [--debug] [--save-to-docs]

company=${1:-"arcade.dev"}
user_id=${2:-"you@example.com"}
shift 2 || true

extra_args=${*:-}

echo "Running demo for company: $company"
echo "User ID: $user_id"

if ! command -v uv >/dev/null 2>&1; then
  echo "Note: 'uv' not found. Falling back to python from current environment." >&2
  python main.py --company "$company" --user-id "$user_id" $extra_args
else
  uv run python main.py --company "$company" --user-id "$user_id" $extra_args
fi

