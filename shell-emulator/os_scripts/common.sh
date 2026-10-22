# Общие функции для скриптов запуска эмулятора.
cd "$(dirname "$0")/.." || exit 1
PYTHON=${PYTHON:-python3}

run() {
    echo
    echo "\$ $PYTHON -m emulator $*"
    "$PYTHON" -m emulator "$@"
    echo "[код завершения эмулятора: $?]"
}
