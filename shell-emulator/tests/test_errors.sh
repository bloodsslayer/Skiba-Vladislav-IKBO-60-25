#!/bin/sh
# Тест ошибок в параметрах командной строки (этап 2)
cd "$(dirname "$0")/.."

echo "=== неизвестный параметр ==="
./emulator --foo

echo "=== --vfs без значения ==="
./emulator --vfs

echo "=== --script без значения ==="
./emulator --script

echo "=== несуществующий скрипт ==="
./emulator --script scripts/no_such_file.txt
