"""Разбор командной строки на слова по правилам UNIX-оболочки (sh).

Поддерживается:
* разделение слов пробелами и табуляцией;
* одинарные кавычки '...' — содержимое берётся буквально;
* двойные кавычки "..." — внутри работает экранирование \\" \\\\ \\$ \\`;
* обратная косая черта вне кавычек экранирует следующий символ;
* склейка соседних частей: a"b c"'d' -> одно слово "ab cd";
* пустые кавычки "" дают пустой аргумент;
* комментарий: # в начале слова вне кавычек — остаток строки игнорируется
  (синтаксис совпадает с комментариями Python и sh);
* ~ в начале слова вне кавычек (~ или ~/путь) заменяется домашним
  каталогом, если он передан в параметре home.
"""


class ParseError(Exception):
    """Синтаксическая ошибка в командной строке."""


_DQUOTE_ESCAPES = '"\\$`'


def split_command(line, home=None):
    words = []
    current = []
    in_word = False  # начато ли слово (нужно, чтобы "" дало пустой аргумент)
    quote = None
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if quote == "'":
            if ch == "'":
                quote = None
            else:
                current.append(ch)
        elif quote == '"':
            if ch == '"':
                quote = None
            elif ch == "\\" and i + 1 < n and line[i + 1] in _DQUOTE_ESCAPES:
                i += 1
                current.append(line[i])
            else:
                current.append(ch)
        elif ch in " \t":
            if in_word:
                words.append("".join(current))
                current, in_word = [], False
        elif ch == "#" and not in_word:
            break
        elif (ch == "~" and not in_word and home is not None
              and (i + 1 == n or line[i + 1] in " \t/")):
            current.append(home.rstrip("/") if i + 1 < n and line[i + 1] == "/" else home)
            in_word = True
        elif ch in "'\"":
            quote, in_word = ch, True
        elif ch == "\\":
            if i + 1 < n:
                i += 1
                current.append(line[i])
            in_word = True
        else:
            current.append(ch)
            in_word = True
        i += 1

    if quote is not None:
        raise ParseError(f"unexpected EOF while looking for matching `{quote}'")
    if in_word:
        words.append("".join(current))
    return words
