#!/bin/sh
# Полный тест всех команд этапов 1-3 на VFS с глубокой вложенностью.
. "$(dirname "$0")/common.sh"
run --vfs vfs/deep.json --script scripts/full_test.vsh
