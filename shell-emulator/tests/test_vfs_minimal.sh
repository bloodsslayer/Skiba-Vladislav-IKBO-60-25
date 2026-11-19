#!/bin/sh
# Тест работы с VFS "minimal" (этап 3)
cd "$(dirname "$0")/.."
./emulator --vfs vfs/minimal.json --script scripts/full.txt
