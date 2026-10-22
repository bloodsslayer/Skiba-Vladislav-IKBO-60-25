#!/bin/sh
# Ошибки в параметрах командной строки.
. "$(dirname "$0")/common.sh"
run --vfs vfs/missing.json                 # VFS не найдена: окно с сообщением
run --script scripts/missing.vsh           # скрипт не найден: окно с сообщением
run --script scripts                       # скрипт - это каталог
run --verbose                              # неизвестная опция: окно не открывается
run --script                               # опция без значения
run --help                                 # справка по параметрам
