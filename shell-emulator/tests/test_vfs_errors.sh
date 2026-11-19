#!/bin/sh
# Тест ошибок загрузки VFS (этап 3)
cd "$(dirname "$0")/.."

echo "=== несуществующий файл VFS ==="
./emulator --vfs vfs/no_such.json --script scripts/full.txt

echo "=== некорректный JSON ==="
./emulator --vfs vfs/broken.json --script scripts/full.txt
