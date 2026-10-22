#!/bin/sh
# Только --script: стартовые скрипты с демонстрацией команд и ошибок.
. "$(dirname "$0")/common.sh"
run --script scripts/demo.vsh
run --script scripts/errors.vsh
