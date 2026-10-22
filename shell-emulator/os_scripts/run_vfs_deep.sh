#!/bin/sh
# VFS: не менее 3 уровней файлов и папок (здесь 6).
. "$(dirname "$0")/common.sh"
run --vfs vfs/deep.json --script scripts/vfs_deep.vsh
