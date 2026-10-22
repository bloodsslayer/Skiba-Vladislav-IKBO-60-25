#!/bin/sh
# Тест работы с VFS "files" (этап 3)
cd "$(dirname "$0")/.."
./emulator --vfs vfs/files.json --script scripts/full.txt
