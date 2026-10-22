#!/bin/sh
# Тест параметров командной строки (этап 2). Закрывайте окно, чтобы перейти к следующему запуску.
cd "$(dirname "$0")/.."

echo "=== без параметров ==="
./emulator

echo "=== только --vfs ==="
./emulator --vfs vfs/minimal.json

echo "=== только --script ==="
./emulator --script scripts/start.txt

echo "=== --vfs и --script ==="
./emulator --vfs vfs/minimal.json --script scripts/start.txt

echo "=== параметры в другом порядке ==="
./emulator --script scripts/start.txt --vfs vfs/minimal.json
