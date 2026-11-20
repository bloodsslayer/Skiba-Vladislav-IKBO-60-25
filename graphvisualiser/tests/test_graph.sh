#!/bin/sh
set -eu

output=$(./build/depviz --test-mode --repo tests/data/test_repo.txt \
    --package A --ascii-tree)

printf '%s\n' "$output" | grep -F '"A" -> "B";' >/dev/null
printf '%s\n' "$output" | grep -F '+-- B' >/dev/null

echo "Tests passed"
