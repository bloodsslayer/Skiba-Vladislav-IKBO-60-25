"""Ядро эмулятора: выполнение команд без привязки к интерфейсу.

Вывод передаётся через функцию write(text, stream), где stream — "out"
или "err"; так ядро работает одинаково в GUI и в тестах.
"""

import getpass
import socket

from .parser import ParseError, split_command
from .vfs import VFS, VFSError

SHELL_NAME = "vsh"


class Shell:
    def __init__(self, write, vfs=None):
        self.write = write
        self.set_vfs(vfs or VFS("vfs"))
        self.user = getpass.getuser()
        self.host = socket.gethostname().split(".")[0]
        self.status = 0          # код завершения последней команды ($?)
        self.exited = False      # была ли выполнена команда exit
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }

    def set_vfs(self, vfs):
        """Подключает VFS; текущим каталогом становится домашний."""
        self.vfs = vfs
        self.cwd = vfs.lookup(vfs.home, vfs.root)
        self.oldpwd = None

    # --- вспомогательное ---------------------------------------------------

    def out(self, text):
        self.write(text + "\n", "out")

    def err(self, text):
        self.write(f"{SHELL_NAME}: {text}\n", "err")

    def cwd_display(self):
        return self.vfs.display_path(self.cwd)

    def prompt(self):
        return f"{self.user}@{self.host}:{self.cwd_display()}$ "

    # --- выполнение ----------------------------------------------------------

    def execute(self, line):
        """Выполняет одну строку и возвращает код завершения."""
        try:
            words = split_command(line, home=self.vfs.home)
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

    def cmd_ls(self, args):
        """ls [-a] [-l] [путь...] — содержимое каталогов VFS."""
        show_all = long = False
        paths = []
        options_done = False
        for arg in args:
            if arg == "--" and not options_done:
                options_done = True
            elif arg.startswith("-") and arg != "-" and not options_done:
                for flag in arg[1:]:
                    if flag == "a":
                        show_all = True
                    elif flag == "l":
                        long = True
                    else:
                        self.write(f"ls: invalid option -- '{flag}'\n", "err")
                        self.write("Usage: ls [-a] [-l] [FILE]...\n", "err")
                        return 2
            else:
                paths.append(arg)

        status = 0
        files, dirs = [], []
        for path in paths or ["."]:
            try:
                node = self.vfs.lookup(path, self.cwd)
            except VFSError as e:
                self.write(f"ls: cannot access '{path}': {e}\n", "err")
                status = 2
                continue
            (dirs if node.is_dir else files).append((path, node))

        for path, node in sorted(files, key=lambda item: item[0]):
            self.out(self._ls_entry(node, path, long))
        dirs.sort(key=lambda item: item[0])
        for i, (path, node) in enumerate(dirs):
            if files or i > 0:
                self.out("")
            if len(paths) > 1:
                self.out(f"{path}:")
            entries = [(name, child) for name, child in sorted(node.children.items())
                       if show_all or not name.startswith(".")]
            if show_all:
                entries = [(".", node), ("..", node.parent or node)] + entries
            if long:
                self.out(f"total {len(entries)}")
                for name, child in entries:
                    self.out(self._ls_entry(child, name, True))
            elif entries:
                self.out("  ".join(name for name, _ in entries))
        return status

    def _ls_entry(self, node, name, long):
        if not long:
            return name
        mode = "drwxr-xr-x" if node.is_dir else "-rw-r--r--"
        return f"{mode} 1 {self.user} {self.user} {node.size:>8} {name}"

    def cmd_cd(self, args):
        """cd [каталог] — смена текущего каталога; без аргумента — домой, "-" — назад."""
        if len(args) > 1:
            self.err("cd: too many arguments")
            return 1
        target = args[0] if args else self.vfs.home
        if target == "-":
            if self.oldpwd is None:
                self.err("cd: OLDPWD not set")
                return 1
            target = self.oldpwd
        try:
            node = self.vfs.lookup(target, self.cwd)
        except VFSError as e:
            self.err(f"cd: {target}: {e}")
            return 1
        if not node.is_dir:
            self.err(f"cd: {target}: Not a directory")
            return 1
        self.oldpwd = self.cwd.path
        self.cwd = node
        if args and args[0] == "-":
            self.out(node.path)
        return 0

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
