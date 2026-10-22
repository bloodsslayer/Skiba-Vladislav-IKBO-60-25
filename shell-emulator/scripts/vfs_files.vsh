# VFS с несколькими файлами, в том числе двоичными (base64).
ls                          # скрытый .hidden не показывается
ls -a
ls -l                       # размеры двоичных файлов - после декодирования base64
ls readme.txt pixel.png     # файлы в аргументах
ls "My Documents"           # каталог с пробелом в имени
cd My\ Documents
ls -l
cd ..
cd readme.txt               # ошибка: не каталог
ls missing.txt              # ошибка: нет файла
