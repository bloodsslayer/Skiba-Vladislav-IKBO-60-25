"""Параметры командной строки эмулятора."""

import argparse
import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_VFS_NAME = "vfs"


@dataclass
class Config:
    vfs: Optional[str] = None      # путь к физическому расположению VFS
    script: Optional[str] = None   # путь к стартовому скрипту

    @property
    def vfs_name(self):
        if not self.vfs:
            return DEFAULT_VFS_NAME
        return os.path.splitext(os.path.basename(os.path.normpath(self.vfs)))[0]

    def debug_lines(self):
        return [
            "[debug] Параметры запуска:",
            f"[debug]   --vfs    = {self.vfs if self.vfs else '(не задан)'}",
            f"[debug]   --script = {self.script if self.script else '(не задан)'}",
            f"[debug]   имя VFS  = {self.vfs_name}",
        ]


def build_parser():
    parser = argparse.ArgumentParser(
        prog="vsh",
        description="Эмулятор командной оболочки UNIX с графическим интерфейсом.",
    )
    parser.add_argument("--vfs", metavar="PATH",
                        help="путь к физическому расположению VFS")
    parser.add_argument("--script", metavar="PATH",
                        help="путь к стартовому скрипту")
    return parser


def parse_args(argv=None):
    """Разбирает argv; при неверных опциях argparse завершает программу с кодом 2."""
    args = build_parser().parse_args(argv)
    return Config(vfs=args.vfs, script=args.script)


def check_paths(config):
    """Проверяет пути из параметров; возвращает список сообщений об ошибках."""
    errors = []
    if config.vfs is not None and not os.path.exists(config.vfs):
        errors.append(f"--vfs: {config.vfs}: No such file or directory")
    if config.script is not None:
        if not os.path.exists(config.script):
            errors.append(f"--script: {config.script}: No such file or directory")
        elif os.path.isdir(config.script):
            errors.append(f"--script: {config.script}: Is a directory")
    return errors


def read_script(path):
    """Читает стартовый скрипт и возвращает список строк (OSError при ошибке)."""
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()
