"""Графический интерфейс: окно, имитирующее терминал UNIX.

Ввод набирается в той же строке, что и приглашение; всё, что выведено
раньше, защищено от редактирования. Поддерживаются история команд
(стрелки вверх/вниз), Ctrl+C (отмена строки или прерывание стартового
скрипта) и Ctrl+L (очистка экрана).
"""

import tkinter as tk

from .config import Config, check_paths, read_script
from .shell import SHELL_NAME, Shell

SCRIPT_DELAY_MS = 150  # пауза между командами стартового скрипта

COLORS = {
    "bg": "#1e1e1e",
    "fg": "#d4d4d4",
    "prompt": "#4ec955",
    "err": "#f14c4c",
    "debug": "#808080",
    "cursor": "#ffffff",
}


class Terminal:
    def __init__(self, root, config=None):
        self.root = root
        self.config = config or Config()
        self.exit_code = 0
        self.history = []
        self.history_pos = 0
        self.busy = False          # выполняется стартовый скрипт
        self.closed = False
        self._script = None

        root.title(f"{SHELL_NAME} — VFS: {self.config.vfs_name}")
        root.geometry("900x560")

        self.text = tk.Text(
            root, wrap="char", undo=False, borderwidth=0, padx=8, pady=6,
            font=("Menlo", 13), bg=COLORS["bg"], fg=COLORS["fg"],
            insertbackground=COLORS["cursor"], selectbackground="#264f78",
        )
        scrollbar = tk.Scrollbar(root, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self.text.tag_configure("prompt", foreground=COLORS["prompt"])
        self.text.tag_configure("err", foreground=COLORS["err"])
        self.text.tag_configure("debug", foreground=COLORS["debug"])

        self.text.bind("<Return>", self._on_return)
        self.text.bind("<KP_Enter>", self._on_return)
        self.text.bind("<BackSpace>", self._on_backspace)
        self.text.bind("<Delete>", self._on_delete)
        self.text.bind("<Up>", lambda e: self._history_step(-1))
        self.text.bind("<Down>", lambda e: self._history_step(1))
        self.text.bind("<Home>", self._on_home)
        self.text.bind("<Control-a>", self._on_home)
        self.text.bind("<Control-c>", self._on_interrupt)
        self.text.bind("<Control-l>", self._on_clear)
        self.text.bind("<Key>", self._on_key, add=True)
        self.text.bind("<<Paste>>", self._on_paste)
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.shell = Shell(self.write)
        self.text.focus_set()
        self.start()

    def start(self):
        """Отладочный вывод параметров, затем стартовый скрипт или диалог."""
        for line in self.config.debug_lines():
            self.write(line + "\n", "debug")
        errors = check_paths(self.config)
        for message in errors:
            self.write(f"{SHELL_NAME}: {message}\n", "err")
        self.write("\n")

        script_ok = self.config.script and not any(m.startswith("--script") for m in errors)
        if not script_ok:
            self.show_prompt()
            return
        try:
            lines = read_script(self.config.script)
        except (OSError, UnicodeDecodeError) as e:
            self.write(f"{SHELL_NAME}: --script: {self.config.script}: {e}\n", "err")
            self.show_prompt()
            return
        self.show_prompt()
        self.run_script(lines)

    # --- вывод --------------------------------------------------------------

    def write(self, text, stream="out"):
        self.text.insert("end", text, (stream,) if stream != "out" else ())
        self.text.see("end")

    def show_prompt(self):
        self.text.insert("end", self.shell.prompt(), ("prompt",))
        self.text.mark_set("input_start", "end-1c")
        self.text.mark_gravity("input_start", "left")
        self.text.mark_set("insert", "end")
        self.text.see("end")

    def current_input(self):
        return self.text.get("input_start", "end-1c")

    def _set_input(self, value):
        self.text.delete("input_start", "end-1c")
        self.text.insert("end", value)
        self.text.see("end")

    # --- выполнение -----------------------------------------------------------

    def run_line(self, line):
        """Выполняет введённую строку: вывод, затем новое приглашение."""
        if line.strip():
            self.history.append(line)
        self.history_pos = len(self.history)
        self.text.insert("end", "\n")
        self.shell.execute(line)
        if self.shell.exited:
            self.exit_code = self.shell.status
            self.close()
            return
        self.show_prompt()

    def close(self):
        self.closed = True
        self._script = None
        self.root.destroy()

    # --- стартовый скрипт --------------------------------------------------------

    def run_script(self, lines):
        """Выполняет строки скрипта по одной, имитируя ввод пользователя."""
        self._script = iter(lines)
        self.busy = True
        self.root.after(SCRIPT_DELAY_MS, self._script_step)

    def _script_step(self):
        if self._script is None or self.closed:
            return
        line = next((l for l in self._script if l.strip()), None)
        if line is None:
            self.stop_script()
            return
        self._set_input(line)
        self.run_line(line)
        if not self.closed:
            self.root.after(SCRIPT_DELAY_MS, self._script_step)

    def stop_script(self):
        self._script = None
        self.busy = False

    # --- обработка клавиш -------------------------------------------------------

    def _in_input(self, index="insert"):
        return self.text.compare(index, ">=", "input_start")

    def _selection_in_history(self):
        ranges = self.text.tag_ranges("sel")
        return bool(ranges) and self.text.compare(ranges[0], "<", "input_start")

    def _move_to_input(self, event=None):
        if not self._in_input():
            self.text.mark_set("insert", "end")

    def _on_paste(self, event):
        if self.busy:
            return "break"
        self._move_to_input()
        return None

    def _on_key(self, event):
        if self.busy and not (event.state & 0x8 or event.state & 0x4):
            return "break"
        # Печатные символы нельзя вставлять в уже выведенный текст.
        if event.char and event.char.isprintable() and not (event.state & 0x8):
            if self._selection_in_history():
                self.text.tag_remove("sel", "1.0", "end")
            self._move_to_input()

    def _on_return(self, event):
        if self.busy:
            return "break"
        line = self.current_input()
        self.text.mark_set("insert", "end")
        self.run_line(line)
        return "break"

    def _on_backspace(self, event):
        if self.busy or self._selection_in_history():
            return "break"
        if self.text.tag_ranges("sel"):
            return None
        if not self.text.compare("insert", ">", "input_start"):
            return "break"
        return None

    def _on_delete(self, event):
        if self.busy or self._selection_in_history() or not self._in_input():
            return "break"
        return None

    def _on_home(self, event):
        self.text.mark_set("insert", "input_start")
        return "break"

    def _on_interrupt(self, event):
        if self.text.tag_ranges("sel"):
            return None  # обычное копирование выделенного текста
        if self.busy:
            self.stop_script()
            self.text.insert("end", "\n[стартовый скрипт прерван]")
        self.text.mark_set("insert", "end")
        self.text.insert("end", "^C\n")
        self.history_pos = len(self.history)
        self.show_prompt()
        return "break"

    def _on_clear(self, event):
        if self.busy:
            return "break"
        line = self.current_input()
        self.text.delete("1.0", "end")
        self.show_prompt()
        self._set_input(line)
        return "break"

    def _history_step(self, step):
        if self.busy or not self.history:
            return "break"
        self.history_pos = max(0, min(len(self.history), self.history_pos + step))
        value = self.history[self.history_pos] if self.history_pos < len(self.history) else ""
        self._set_input(value)
        return "break"


def run(config=None):
    root = tk.Tk()
    terminal = Terminal(root, config)
    root.mainloop()
    return terminal.exit_code
