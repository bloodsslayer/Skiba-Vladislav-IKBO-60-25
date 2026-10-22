import base64
import json
import os
import tempfile
import unittest

from emulator.shell import Shell
from emulator.vfs import VFS, VFSError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPEC = {
    "name": "test",
    "home": "/home/user",
    "root": {"type": "dir", "children": {
        "etc": {"type": "dir", "children": {
            "passwd": {"type": "file", "content": "root"},
        }},
        "home": {"type": "dir", "children": {
            "user": {"type": "dir", "children": {
                ".profile": {"type": "file", "content": ""},
                "docs": {"type": "dir", "children": {
                    "a b.txt": {"type": "file", "content": "текст"},
                    "img.bin": {"type": "file", "encoding": "base64",
                                "content": base64.b64encode(bytes(range(10))).decode()},
                }},
            }},
        }},
    }},
}


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_json(tmp, data, name="v.json"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data if isinstance(data, str) else json.dumps(data))
    return path


class LoadTest(unittest.TestCase):
    def test_load_from_dict(self):
        vfs = VFS.from_dict(SPEC)
        self.assertEqual((vfs.name, vfs.home), ("test", "/home/user"))
        self.assertEqual(vfs.stats(), (5, 4))

    def test_base64_is_decoded_in_memory(self):
        vfs = VFS.from_dict(SPEC)
        node = vfs.lookup("/home/user/docs/img.bin", vfs.root)
        self.assertEqual(node.data, bytes(range(10)))
        self.assertEqual(vfs.lookup("/home/user/docs/a b.txt", vfs.root).size, len("текст".encode()))

    def test_source_file_is_not_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_json(tmp, SPEC)
            before = read_bytes(path)
            shell = Shell(lambda *a: None, VFS.load(path))
            for line in ("cd docs", "ls -la", "cd /etc", "ls passwd"):
                shell.execute(line)
            self.assertEqual(read_bytes(path), before)
            self.assertEqual(os.listdir(tmp), ["v.json"])

    def test_name_defaults_to_file_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_json(tmp, {"root": {"type": "dir"}}, "my_fs.json")
            self.assertEqual(VFS.load(path).name, "my_fs")

    def test_load_errors(self):
        bad = {
            "missing root": {"name": "x"},
            "root is file": {"root": {"type": "file"}},
            "unknown type": {"root": {"type": "dir", "children": {"l": {"type": "link"}}}},
            "bad base64": {"root": {"type": "dir", "children": {
                "f": {"type": "file", "encoding": "base64", "content": "!!!"}}}},
            "bad encoding": {"root": {"type": "dir", "children": {
                "f": {"type": "file", "encoding": "utf-16", "content": ""}}}},
            "bad name": {"root": {"type": "dir", "children": {"a/b": {"type": "file"}}}},
            "home is file": {"home": "/f", "root": {"type": "dir", "children": {"f": {"type": "file"}}}},
            "home missing": {"home": "/nope", "root": {"type": "dir"}},
            "not an object": [1, 2],
        }
        for case, data in bad.items():
            with self.subTest(case=case), self.assertRaises(VFSError):
                VFS.from_dict(data)

    def test_file_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = {
                os.path.join(tmp, "none.json"): "No such file",
                tmp: "Is a directory",
                write_json(tmp, "{broken"): "некорректный JSON",
            }
            for path, message in cases.items():
                with self.subTest(path=path), self.assertRaises(VFSError) as cm:
                    VFS.load(path)
                self.assertIn(message, str(cm.exception))

    def test_examples(self):
        for name, ok in [("minimal", True), ("files", True), ("deep", True),
                         ("broken_json", False), ("bad_base64", False), ("bad_node", False),
                         ("root_is_file", False), ("no_root", False)]:
            path = os.path.join(ROOT, "vfs", name + ".json")
            with self.subTest(name=name):
                if ok:
                    VFS.load(path)
                else:
                    self.assertRaises(VFSError, VFS.load, path)

    def test_deep_example_has_at_least_three_levels(self):
        vfs = VFS.load(os.path.join(ROOT, "vfs", "deep.json"))
        self.assertFalse(vfs.lookup("/home/user/docs/reports/2024/q1.txt", vfs.root).is_dir)


class LookupTest(unittest.TestCase):
    def setUp(self):
        self.vfs = VFS.from_dict(SPEC)
        self.home = self.vfs.lookup("/home/user", self.vfs.root)

    def path(self, p, cwd=None):
        return self.vfs.lookup(p, cwd or self.home).path

    def test_relative_and_absolute(self):
        self.assertEqual(self.path("docs"), "/home/user/docs")
        self.assertEqual(self.path("/etc/"), "/etc")
        self.assertEqual(self.path("./docs/../../user/."), "/home/user")
        self.assertEqual(self.path("../../../.."), "/")

    def test_errors(self):
        for p, message in [("nope", "No such file"), ("/etc/passwd/x", "Not a directory"),
                           ("/etc/passwd/", "Not a directory")]:
            with self.subTest(p=p), self.assertRaises(VFSError) as cm:
                self.vfs.lookup(p, self.home)
            self.assertIn(message, str(cm.exception))

    def test_display_path(self):
        docs = self.vfs.lookup("docs", self.home)
        self.assertEqual(self.vfs.display_path(docs), "~/docs")
        self.assertEqual(self.vfs.display_path(self.vfs.root), "/")


class CommandsTest(unittest.TestCase):
    def setUp(self):
        self.output = []
        self.shell = Shell(lambda text, stream="out": self.output.append((stream, text)),
                           VFS.from_dict(SPEC))

    def run_line(self, line):
        self.output.clear()
        status = self.shell.execute(line)
        out = "".join(t for s, t in self.output if s == "out")
        err = "".join(t for s, t in self.output if s == "err")
        return status, out, err

    def test_starts_in_home(self):
        self.assertTrue(self.shell.prompt().endswith(":~$ "))

    def test_ls(self):
        self.assertEqual(self.run_line("ls"), (0, "docs\n", ""))
        self.assertEqual(self.run_line("ls -a")[1], ".  ..  .profile  docs\n")
        self.assertEqual(self.run_line('ls "docs/a b.txt"')[1], "docs/a b.txt\n")
        self.assertEqual(self.run_line("ls / /etc")[1], "/:\netc  home\n\n/etc:\npasswd\n")

    def test_ls_long_shows_decoded_size(self):
        out = self.run_line("ls -l docs")[1]
        self.assertIn("total 2", out)
        self.assertRegex(out, r"-rw-r--r-- .* 10 img\.bin")

    def test_ls_errors(self):
        status, out, err = self.run_line("ls nope docs")
        self.assertEqual(status, 2)
        self.assertEqual(err, "ls: cannot access 'nope': No such file or directory\n")
        self.assertIn("a b.txt", out)
        status, _, err = self.run_line("ls -q")
        self.assertEqual(status, 2)
        self.assertIn("invalid option -- 'q'", err)

    def test_cd(self):
        self.assertEqual(self.run_line("cd docs")[0], 0)
        self.assertTrue(self.shell.prompt().endswith(":~/docs$ "))
        self.run_line("cd ../../..")
        self.assertEqual(self.shell.cwd.path, "/")
        self.assertEqual(self.run_line("cd -"), (0, "/home/user/docs\n", ""))
        self.run_line("cd")
        self.assertEqual(self.shell.cwd.path, "/home/user")
        self.run_line("cd ~/docs")
        self.assertEqual(self.shell.cwd.path, "/home/user/docs")

    def test_cd_errors(self):
        cases = [
            ("cd -", "vsh: cd: OLDPWD not set\n"),
            ("cd nope", "vsh: cd: nope: No such file or directory\n"),
            ("cd /etc/passwd", "vsh: cd: /etc/passwd: Not a directory\n"),
            ("cd /etc /home", "vsh: cd: too many arguments\n"),
            ('cd "~"', "vsh: cd: ~: No such file or directory\n"),
        ]
        for line, message in cases:
            with self.subTest(line=line):
                status, _, err = self.run_line(line)
                self.assertEqual((status, err), (1, message))
                self.assertEqual(self.shell.cwd.path, "/home/user")


if __name__ == "__main__":
    unittest.main()
