# vsh — эмулятор командной оболочки UNIX (вариант 26)

Эмулятор языка оболочки ОС с графическим интерфейсом. Работа максимально
похожа на командную строку UNIX-подобной ОС: приглашение
`пользователь@хост:каталог$`, ввод в той же строке, сообщения об ошибках в
стиле bash, коды завершения.

Написан на Python 3 со стандартной библиотекой; GUI — `tkinter`.

## Запуск

```
python3 -m emulator
```

> На macOS с Python из Homebrew tkinter ставится отдельно:
> `brew install python-tk@3.14`.

## Возможности

* **GUI-терминал.** Заголовок окна содержит имя VFS. Уже выведенный текст
  защищён от редактирования, ↑/↓ — история команд, Ctrl+C — отмена строки,
  Ctrl+L — очистка экрана.
* **Парсер** (`emulator/parser.py`, без `shlex`) по правилам sh:
  * `"..."` — двойные кавычки, внутри работают `\"`, `\\`, `\$`, `` \` ``;
  * `'...'` — одинарные кавычки, содержимое берётся буквально;
  * `\` вне кавычек экранирует следующий символ (`My\ Docs`);
  * соседние части склеиваются (`a"b c"'d'` → `ab cd`);
  * `""` даёт пустой аргумент;
  * незакрытая кавычка — синтаксическая ошибка.
* **Команды**
  * `ls`, `cd` — заглушки: выводят своё имя и полученные аргументы
    (каждый аргумент в `[...]`, чтобы были видны границы слов);
  * `exit [N]` — выход из эмулятора с кодом `N` (по умолчанию — код
    последней команды).
* **Ошибки** (как в bash): неизвестная команда — код 127, синтаксическая
  ошибка — код 2, `exit abc` — `numeric argument required`,
  `exit 1 2` — `too many arguments` (эмулятор не закрывается).

## Демонстрация (интерактивный режим)

Запустите `python3 -m emulator` и введите:

```
ls
ls -l "My Documents" 'a b' c\ d
cd "/home/user"
cd ""
ls a"b c"'d e'
ls "say \"hi\""
ls "unclosed
pwd
exit 1 2
exit abc
```

Ожидаемый вывод:

```
user@host:~$ ls
ls: аргументы: (нет аргументов)
user@host:~$ ls -l "My Documents" 'a b' c\ d
ls: аргументы: [-l] [My Documents] [a b] [c d]
user@host:~$ cd "/home/user"
cd: аргументы: [/home/user]
user@host:~$ cd ""
cd: аргументы: []
user@host:~$ ls a"b c"'d e'
ls: аргументы: [ab cd e]
user@host:~$ ls "say \"hi\""
ls: аргументы: [say "hi"]
user@host:~$ ls "unclosed
vsh: syntax error: unexpected EOF while looking for matching `"'
user@host:~$ pwd
vsh: pwd: command not found
user@host:~$ exit 1 2
vsh: exit: too many arguments
user@host:~$ exit abc
vsh: exit: abc: numeric argument required
```

После `exit abc` окно закрывается с кодом 2 (`echo $?` в терминале ОС).

## Тесты

```
python3 -m unittest -v
```
