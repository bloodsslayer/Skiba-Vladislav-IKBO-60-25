#!/bin/sh
# Ошибки загрузки VFS: эмулятор сообщает об ошибке и работает с пустой VFS.
. "$(dirname "$0")/common.sh"
run --vfs vfs/missing.json --script scripts/vfs_minimal.vsh      # файла нет
run --vfs vfs --script scripts/vfs_minimal.vsh                   # каталог вместо файла
run --vfs vfs/broken_json.json --script scripts/vfs_minimal.vsh  # синтаксис JSON
run --vfs vfs/no_root.json --script scripts/vfs_minimal.vsh      # нет поля root
run --vfs vfs/root_is_file.json --script scripts/vfs_minimal.vsh # корень - файл
run --vfs vfs/bad_node.json --script scripts/vfs_minimal.vsh     # неизвестный тип узла
run --vfs vfs/bad_base64.json --script scripts/vfs_minimal.vsh   # битый base64
