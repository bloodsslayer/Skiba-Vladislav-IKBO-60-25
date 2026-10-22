#!/bin/sh
# Тест работы с VFS "deep" (этап 3)
cd "$(dirname "$0")/.."
./emulator --vfs vfs/deep.json --script scripts/full.txt
