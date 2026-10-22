import os
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO

from emulator.config import Config, check_paths, parse_args, read_script


class ParseArgsTest(unittest.TestCase):
    def test_defaults(self):
        config = parse_args([])
        self.assertEqual((config.vfs, config.script), (None, None))
        self.assertEqual(config.vfs_name, "vfs")

    def test_all_params(self):
        config = parse_args(["--vfs", "vfs/minimal.json", "--script", "s.vsh"])
        self.assertEqual(config.vfs, "vfs/minimal.json")
        self.assertEqual(config.script, "s.vsh")
        self.assertEqual(config.vfs_name, "minimal")

    def test_debug_lines_contain_all_params(self):
        text = "\n".join(Config("a/b.json", "c.vsh").debug_lines())
        for value in ("--vfs", "a/b.json", "--script", "c.vsh", "b"):
            self.assertIn(value, text)

    def test_invalid_options(self):
        for argv in (["--verbose"], ["--script"], ["extra"]):
            with self.subTest(argv=argv), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    parse_args(argv)
                self.assertEqual(cm.exception.code, 2)


class PathsTest(unittest.TestCase):
    def test_missing_script(self):
        # Путь к VFS проверяет загрузчик VFS (tests/test_vfs.py).
        errors = check_paths(Config("/no/such.json", "/no/such.vsh"))
        self.assertEqual(errors, ["--script: /no/such.vsh: No such file or directory"])

    def test_script_is_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(check_paths(Config(script=tmp)), [f"--script: {tmp}: Is a directory"])

    def test_read_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.vsh")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# c\nls\n")
            self.assertEqual(read_script(path), ["# c", "ls"])
            self.assertEqual(check_paths(Config(script=path)), [])


if __name__ == "__main__":
    unittest.main()
