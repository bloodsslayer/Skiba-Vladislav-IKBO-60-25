#!/bin/sh
# VFS: минимальная (пустой корень).
. "$(dirname "$0")/common.sh"
run --vfs vfs/minimal.json --script scripts/vfs_minimal.vsh
