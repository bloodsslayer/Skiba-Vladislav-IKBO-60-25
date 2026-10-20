"""Графический интерфейс: окно, имитирующее терминал UNIX.

Ввод набирается в той же строке, что и приглашение; всё, что выведено
раньше, защищено от редактирования. Поддерживаются история команд
(стрелки вверх/вниз), Ctrl+C (отмена строки) и Ctrl+L (очистка экрана).
"""

import tkinter as tk

from .shell import SHELL_NAME, Shell

DEFAULT_VFS_NAME = "vfs"

COLORS = {
    "bg": "#1e1e1e",
    "fg": "#d4d4d4",
    "prompt": "#4ec955",
    "err": "#f14c4c",
    "cursor": "#ffffff",
}


class Terminal:
    def __init__(self, root, vfs_name=DEFAULT_VFS_NAME):
        self.root = root
        self.vfs_name = vfs_name
        self.exit_code = 0
        self.history = []
        self.history_pos = 0

        root.title(f"{SHELL_NAME} — VFS: {vfs_name}")
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
        self.text.bind("<<Paste>>", self._move_to_input, add=True)
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.shell = Shell(self.write)
        self.show_prompt()
        self.text.focus_set()

    # --- вывод --------------------------------------------------------------

    def write(self, text, stream="out"):
        self.text.insert("end", text, ("err",) if stream == "err" else ())
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
        self.root.destroy()

    # --- обработка клавиш -------------------------------------------------------

    def _in_input(self, index="insert"):
        return self.text.compare(index, ">=", "input_start")

    def _selection_in_history(self):
        ranges = self.text.tag_ranges("sel")
        return bool(ranges) and self.text.compare(ranges[0], "<", "input_start")

    def _move_to_input(self, event=None):
        if not self._in_input():
            self.text.mark_set("insert", "end")

    def _on_key(self, event):
        # Печатные символы нельзя вставлять в уже выведенный текст.
        if event.char and event.char.isprintable() and not (event.state & 0x8):
            if self._selection_in_history():
                self.text.tag_remove("sel", "1.0", "end")
            self._move_to_input()

    def _on_return(self, event):
        line = self.current_input()
        self.text.mark_set("insert", "end")
        self.run_line(line)
        return "break"

    def _on_backspace(self, event):
        if self._selection_in_history():
            return "break"
        if self.text.tag_ranges("sel"):
            return None
        if not self.text.compare("insert", ">", "input_start"):
            return "break"
        return None

    def _on_delete(self, event):
        if self._selection_in_history() or not self._in_input():
            return "break"
        return None

    def _on_home(self, event):
        self.text.mark_set("insert", "input_start")
        return "break"

    def _on_interrupt(self, event):
        if self.text.tag_ranges("sel"):
            return None  # обычное копирование выделенного текста
        self.text.mark_set("insert", "end")
        self.text.insert("end", "^C\n")
        self.history_pos = len(self.history)
        self.show_prompt()
        return "break"

    def _on_clear(self, event):
        line = self.current_input()
        self.text.delete("1.0", "end")
        self.show_prompt()
        self._set_input(line)
        return "break"

    def _history_step(self, step):
        if not self.history:
            return "break"
        self.history_pos = max(0, min(len(self.history), self.history_pos + step))
        value = self.history[self.history_pos] if self.history_pos < len(self.history) else ""
        self._set_input(value)
        return "break"


def run(vfs_name=DEFAULT_VFS_NAME):
    root = tk.Tk()
    terminal = Terminal(root, vfs_name)
    root.mainloop()
    return terminal.exit_code
