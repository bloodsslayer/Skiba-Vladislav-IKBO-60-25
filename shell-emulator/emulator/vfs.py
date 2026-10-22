"""Виртуальная файловая система (VFS), целиком хранящаяся в памяти.

Источник — JSON-файл. Он только читается: VFS загружается в память, и
все операции выполняются над объектами в памяти, файл не изменяется.

Формат:

    {
      "name": "demo",                  # имя VFS (необязательно)
      "home": "/home/user",            # домашний каталог (необязательно, "/")
      "root": {                        # корневой каталог
        "type": "dir",
        "children": {
          "readme.txt": {"type": "file", "content": "текст"},
          "logo.png":   {"type": "file", "encoding": "base64",
                         "content": "iVBORw0KGgo..."},
          "home": {"type": "dir", "children": {...}}
        }
      }
    }

Содержимое файла — строка в UTF-8 ("encoding": "text", по умолчанию)
или двоичные данные в base64 ("encoding": "base64").
"""

import base64
import binascii
import json
import os


class VFSError(Exception):
    """Ошибка загрузки VFS или обращения к ней."""


class Node:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    @property
    def path(self):
        parts = []
        node = self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))


class Directory(Node):
    is_dir = True

    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.children = {}

    @property
    def size(self):
        return len(self.children)


class File(Node):
    is_dir = False

    def __init__(self, name, data, parent=None):
        super().__init__(name, parent)
        self.data = data  # bytes

    @property
    def size(self):
        return len(self.data)


# --- загрузка -------------------------------------------------------------------

def _check_name(name, where):
    if not isinstance(name, str) or name in ("", ".", "..") or "/" in name:
        raise VFSError(f"{where}: недопустимое имя '{name}'")


def _build(spec, name, parent, where):
    if not isinstance(spec, dict):
        raise VFSError(f"{where}: описание узла должно быть объектом JSON")
    kind = spec.get("type")
    if kind == "dir":
        node = Directory(name, parent)
        children = spec.get("children", {})
        if not isinstance(children, dict):
            raise VFSError(f"{where}: поле 'children' должно быть объектом")
        for child_name, child_spec in children.items():
            child_where = where.rstrip("/") + "/" + str(child_name)
            _check_name(child_name, child_where)
            node.children[child_name] = _build(child_spec, child_name, node, child_where)
        return node
    if kind == "file":
        content = spec.get("content", "")
        if not isinstance(content, str):
            raise VFSError(f"{where}: поле 'content' должно быть строкой")
        encoding = spec.get("encoding", "text")
        if encoding == "text":
            data = content.encode("utf-8")
        elif encoding == "base64":
            try:
                data = base64.b64decode(content, validate=True)
            except (binascii.Error, ValueError) as e:
                raise VFSError(f"{where}: некорректные данные base64 ({e})") from e
        else:
            raise VFSError(f"{where}: неизвестная кодировка '{encoding}' (ожидается text или base64)")
        return File(name, data, parent)
    raise VFSError(f"{where}: неизвестный тип узла {kind!r} (ожидается 'dir' или 'file')")


class VFS:
    def __init__(self, name, root=None, home="/"):
        self.name = name
        self.root = root if root is not None else Directory("")
        self.home = home

    @classmethod
    def from_dict(cls, data, default_name="vfs"):
        if not isinstance(data, dict):
            raise VFSError("ожидается объект JSON с полем 'root'")
        if "root" not in data:
            raise VFSError("нет поля 'root' с корневым каталогом")
        name = data.get("name", default_name)
        if not isinstance(name, str) or not name:
            raise VFSError("поле 'name' должно быть непустой строкой")
        root = _build(data["root"], "", None, "/")
        if not root.is_dir:
            raise VFSError("корень VFS должен быть каталогом (\"type\": \"dir\")")
        vfs = cls(name, root)
        home = data.get("home", "/")
        if not isinstance(home, str) or not home.startswith("/"):
            raise VFSError("поле 'home' должно быть абсолютным путём")
        node = vfs.lookup(home, root)
        if not node.is_dir:
            raise VFSError(f"домашний каталог {home} не является каталогом")
        vfs.home = node.path
        return vfs

    @classmethod
    def load(cls, path):
        default_name = os.path.splitext(os.path.basename(os.path.normpath(path)))[0]
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise VFSError("No such file or directory") from None
        except IsADirectoryError:
            raise VFSError("Is a directory") from None
        except json.JSONDecodeError as e:
            raise VFSError(f"некорректный JSON: {e.msg} (строка {e.lineno}, столбец {e.colno})") from e
        except (OSError, UnicodeDecodeError) as e:
            raise VFSError(str(e)) from e
        return cls.from_dict(data, default_name)

    # --- пути ---------------------------------------------------------------------

    def lookup(self, path, cwd):
        """Возвращает узел по абсолютному или относительному пути.

        Бросает VFSError("No such file or directory") или
        VFSError("Not a directory"), как стандартные утилиты UNIX.
        """
        node = self.root if path.startswith("/") else cwd
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if not node.is_dir:
                raise VFSError("Not a directory")
            if part == "..":
                node = node.parent or node
                continue
            child = node.children.get(part)
            if child is None:
                raise VFSError("No such file or directory")
            node = child
        if path.endswith("/") and not node.is_dir:
            raise VFSError("Not a directory")
        return node

    def display_path(self, node):
        """Путь для приглашения: домашний каталог заменяется на ~."""
        path, home = node.path, self.home
        if home != "/" and (path == home or path.startswith(home + "/")):
            return "~" + path[len(home):]
        return path

    def stats(self):
        dirs = files = 0
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.is_dir:
                dirs += 1
                stack.extend(node.children.values())
            else:
                files += 1
        return dirs, files
