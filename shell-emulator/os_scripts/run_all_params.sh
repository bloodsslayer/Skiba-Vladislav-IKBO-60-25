#!/bin/sh
# Все параметры сразу; скрипт exit.vsh сам закрывает эмулятор с кодом 5.
. "$(dirname "$0")/common.sh"
run --vfs vfs/minimal.json --script scripts/exit.vsh
