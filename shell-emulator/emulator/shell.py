"""Ядро эмулятора: выполнение команд без привязки к интерфейсу.

Вывод передаётся через функцию write(text, stream), где stream — "out"
или "err"; так ядро работает одинаково в GUI и в тестах.
"""

import getpass
import socket

from .parser import ParseError, split_command

SHELL_NAME = "vsh"


class Shell:
    def __init__(self, write):
        self.write = write
        self.user = getpass.getuser()
        self.host = socket.gethostname().split(".")[0]
        self.status = 0          # код завершения последней команды ($?)
        self.exited = False      # была ли выполнена команда exit
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }

    # --- вспомогательное ---------------------------------------------------

    def out(self, text):
        self.write(text + "\n", "out")

    def err(self, text):
        self.write(f"{SHELL_NAME}: {text}\n", "err")

    def cwd_display(self):
        return "~"

    def prompt(self):
        return f"{self.user}@{self.host}:{self.cwd_display()}$ "

    # --- выполнение ----------------------------------------------------------

    def execute(self, line):
        """Выполняет одну строку и возвращает код завершения."""
        try:
            words = split_command(line)
        except ParseError as e:
            self.err(f"syntax error: {e}")
            self.status = 2
            return self.status
        if not words:
            return self.status

        name, args = words[0], words[1:]
        command = self.commands.get(name)
        if command is None:
            self.err(f"{name}: command not found")
            self.status = 127
        else:
            self.status = command(args)
        return self.status

    # --- команды -----------------------------------------------------------

    def _stub(self, name, args):
        """Заглушка: печатает имя команды и полученные аргументы."""
        shown = " ".join(f"[{arg}]" for arg in args) if args else "(нет аргументов)"
        self.out(f"{name}: аргументы: {shown}")
        return 0

    def cmd_ls(self, args):
        return self._stub("ls", args)

    def cmd_cd(self, args):
        return self._stub("cd", args)

    def cmd_exit(self, args):
        if len(args) > 1:
            self.err("exit: too many arguments")
            return 1
        code = self.status
        if args:
            try:
                code = int(args[0]) % 256
            except ValueError:
                self.err(f"exit: {args[0]}: numeric argument required")
                code = 2
        self.exited = True
        return code
