import unittest

from emulator.parser import ParseError, split_command


class SplitCommandTest(unittest.TestCase):
    def check(self, line, expected):
        self.assertEqual(split_command(line), expected)

    def test_plain_words(self):
        self.check("ls  -l\t/tmp ", ["ls", "-l", "/tmp"])

    def test_empty_line(self):
        self.check("   ", [])

    def test_double_quotes(self):
        self.check('cd "My Documents"', ["cd", "My Documents"])

    def test_single_quotes_are_literal(self):
        self.check(r"ls 'a \" b'", ["ls", r'a \" b'])

    def test_escapes_inside_double_quotes(self):
        self.check(r'ls "say \"hi\" \\ \n"', ["ls", r'say "hi" \ \n'])

    def test_backslash_outside_quotes(self):
        self.check(r"ls a\ b \'c", ["ls", "a b", "'c"])

    def test_adjacent_parts_are_joined(self):
        self.check("""ls a"b c"'d e'f""", ["ls", "ab cd ef"])

    def test_empty_quotes_give_empty_argument(self):
        self.check("""cd "" ''""", ["cd", "", ""])

    def test_comments(self):
        self.check("# только комментарий", [])
        self.check("ls -l   # комментарий", ["ls", "-l"])
        self.check("ls a#b '#c' \\#d", ["ls", "a#b", "#c", "#d"])

    def test_tilde_expansion(self):
        self.assertEqual(
            split_command("""ls ~ ~/docs "~" '~/x' ~user a~ \\~""", home="/home/u"),
            ["ls", "/home/u", "/home/u/docs", "~", "~/x", "~user", "a~", "~"],
        )
        self.assertEqual(split_command("cd ~/a", home="/"), ["cd", "/a"])
        self.assertEqual(split_command("cd ~"), ["cd", "~"])

    def test_unterminated_quotes(self):
        for line in ('ls "abc', "ls 'abc", 'ls "a\\"'):
            with self.subTest(line=line), self.assertRaises(ParseError):
                split_command(line)


if __name__ == "__main__":
    unittest.main()
