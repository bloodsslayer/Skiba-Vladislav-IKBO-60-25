import os
import re
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = os.environ.get("CONFIG_TO_TOML", ROOT / "build/config-to-toml")


class ConverterTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.output = Path(folder.name) / "result.toml"

    def run_cli(self, source, *args):
        return subprocess.run(
            [PROGRAM, *args], input=source, capture_output=True,
            encoding="utf-8", timeout=5,
        )

    def convert(self, source, expected):
        result = self.run_cli(source, "-o", self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertTrue(self.output.is_file(), "Файл TOML не создан")
        with self.output.open("rb") as output:
            self.assertEqual(tomllib.load(output), expected)

    def check_error(self, source, message, position=None):
        result = self.run_cli(source, "-o", self.output)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(message, result.stderr)
        if position:
            self.assertIn(position, result.stderr)

    def test_numbers(self):
        self.convert(
            "table(a => 1.25, b => -2.5, c => +0003.50, d => -00.0)",
            {"a": 1.25, "b": -2.5, "c": 3.5, "d": -0.0},
        )
        self.assertIn("d = -0.0", self.output.read_text(encoding="utf-8"))

    def test_strings(self):
        self.convert(
            'table(a => @"Привет # Мир", b => @"", c => @"C:\\new\t\n\x01\x7f")',
            {"a": "Привет # Мир", "b": "", "c": "C:\\new\t\n\x01\x7f"},
        )

    def test_nested_and_empty_tables(self):
        self.convert(
            "table(def => table(table => table(), item => 1.0,), item => 2.0,)",
            {"def": {"table": {}, "item": 1.0}, "item": 2.0},
        )

    def test_empty_root(self):
        self.convert("table()", {})

    def test_constants_of_all_types(self):
        self.convert(
            """
            (def number +04.0)
            (def label @"Текст")
            (def alias $number$)
            (def settings table(name => $label$, nested => table(scale => $alias$)))
            table(first => $settings$, second => table(copy => $settings$), text => $label$)
            """,
            {
                "first": {"name": "Текст", "nested": {"scale": 4.0}},
                "second": {"copy": {"name": "Текст", "nested": {"scale": 4.0}}},
                "text": "Текст",
            },
        )

    def test_dictionary_constant_as_root(self):
        self.convert("(def table table(def => -1.0))\r\n$table$", {"def": -1.0})

    def test_invalid_numbers(self):
        for number in ("2", ".2", "2.", "2e2", "-.2", "+ 2.0", "1.2e3"):
            with self.subTest(number=number):
                self.check_error(f"table(a => {number})", "Ошибка")

    def test_invalid_syntax(self):
        cases = (
            "", "table(Upper => 1.0)", "table(a1 => 1.0)",
            "table(a = 1.0)", "table(a => 1.0 b => 2.0)",
            "table(a => table(b => 1.0)", "table(a => 1.0,,)",
            "table(,)", "table(a => $foo)", "table(a => $ foo $)",
            'table(a => "текст")', 'table(a => @"незакрытая строка)',
            "(def a 1.0 table()", "table(a => (def b 1.0))", "table() table()",
        )
        for source in cases:
            with self.subTest(source=source):
                self.check_error(source, "Ошибка")
                self.assertFalse(self.output.exists())

    def test_semantic_errors(self):
        cases = (
            ("table(a => $missing$)", "Неизвестная константа"),
            ("(def a $b$) (def b 1.0) table()", "Неизвестная константа"),
            ("(def a 1.0) (def a 2.0) table()", "Константа уже объявлена"),
            ("table(a => table(b => 1.0, b => 2.0))", "Повторяющийся ключ"),
            ("(def a 1.0) $a$", "Корневое значение должно быть словарём"),
        )
        for source, message in cases:
            with self.subTest(source=source):
                self.check_error(source, message)

    def test_error_location_and_existing_output(self):
        self.output.write_text("existing", encoding="utf-8")
        self.check_error("table(\n  key => $unknown$\n)", "Неизвестная", "2:10")
        self.assertEqual(self.output.read_text(encoding="utf-8"), "existing")

    def test_command_line_errors(self):
        for args in ((), ("-o",), ("-x", self.output)):
            with self.subTest(args=args):
                result = self.run_cli("table()", *args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("-o", result.stderr)
        result = self.run_cli("table()", "-o", self.output / "absent.toml")
        self.assertEqual(result.returncode, 1)
        self.assertIn("открыть файл", result.stderr)

    def test_readme_examples(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        examples = re.findall(r"```text\n(.*?)```\s*```toml\n(.*?)```", readme, re.S)
        self.assertEqual(len(examples), 3)
        for source, output in examples:
            with self.subTest(source=source):
                self.convert(source, tomllib.loads(output))


if __name__ == "__main__":
    unittest.main()
