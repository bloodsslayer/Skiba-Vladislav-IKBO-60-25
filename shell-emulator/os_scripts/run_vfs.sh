#!/bin/sh
# Только --vfs: имя VFS в заголовке окна берётся из имени файла.
. "$(dirname "$0")/common.sh"
run --vfs vfs/minimal.json
