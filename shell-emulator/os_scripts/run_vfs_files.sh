#!/bin/sh
# VFS: несколько файлов, включая двоичные в base64.
. "$(dirname "$0")/common.sh"
run --vfs vfs/files.json --script scripts/vfs_files.vsh
