import unittest

from emulator.shell import Shell


class ShellTestCase(unittest.TestCase):
    def setUp(self):
        self.output = []
        self.shell = Shell(lambda text, stream="out": self.output.append((stream, text)))

    def run_line(self, line):
        self.output.clear()
        status = self.shell.execute(line)
        return status, "".join(text for _, text in self.output)

    def errors(self):
        return "".join(text for stream, text in self.output if stream == "err")


class StubCommandsTest(ShellTestCase):
    def test_ls_prints_name_and_args(self):
        status, out = self.run_line('ls -l "My Documents"')
        self.assertEqual(status, 0)
        self.assertEqual(out, "ls: аргументы: [-l] [My Documents]\n")

    def test_cd_without_args(self):
        self.assertEqual(self.run_line("cd")[1], "cd: аргументы: (нет аргументов)\n")

    def test_unknown_command(self):
        status, _ = self.run_line("pwd")
        self.assertEqual(status, 127)
        self.assertEqual(self.errors(), "vsh: pwd: command not found\n")

    def test_syntax_error(self):
        status, _ = self.run_line('ls "abc')
        self.assertEqual(status, 2)
        self.assertIn("syntax error", self.errors())

    def test_empty_line_keeps_status(self):
        self.run_line("pwd")
        self.assertEqual(self.run_line("")[0], 127)

    def test_prompt(self):
        self.assertTrue(self.shell.prompt().endswith(":~$ "))
        self.assertIn("@", self.shell.prompt())


class ExitTest(ShellTestCase):
    def test_exit_uses_last_status(self):
        self.run_line("pwd")
        self.assertEqual(self.run_line("exit")[0], 127)
        self.assertTrue(self.shell.exited)

    def test_exit_with_code(self):
        self.assertEqual(self.run_line("exit 300")[0], 300 % 256)
        self.assertTrue(self.shell.exited)

    def test_exit_not_a_number(self):
        self.assertEqual(self.run_line("exit abc")[0], 2)
        self.assertTrue(self.shell.exited)

    def test_exit_too_many_arguments(self):
        self.assertEqual(self.run_line("exit 1 2")[0], 1)
        self.assertFalse(self.shell.exited)


if __name__ == "__main__":
    unittest.main()
