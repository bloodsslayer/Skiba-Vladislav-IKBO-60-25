# Практическое занятие №1. Введение, основы работы в командной строке
Научиться выполнять простые действия с файлами и каталогами в Linux из командной строки. Сравнить работу в командной строке Windows и Linux.
  
  
## Задача 1
Вывести отсортированный в алфавитном порядке список имен пользователей в файле passwd (вам понадобится grep).  
```
cd /etc
grep -o "^[^:]*" passwd | sort
```
<img width="615" height="485" alt="1" src="https://github.com/user-attachments/assets/0cef54f0-b7d6-4ac7-a05c-1da51feae2e3" />



## Задача 2
Вывести данные /etc/protocols в отформатированном и отсортированном порядке для 5 наибольших портов.  
```
awk '{print $2,$1}' protocols | sort -r | head -5
```
<img width="616" height="85" alt="2" src="https://github.com/user-attachments/assets/b2388593-e51c-4295-9633-df3c71305559" />



## Задача 3
Написать программу banner средствами bash для вывода текстов, как в следующем примере (размер баннера должен меняться!).  
```
nano banner
```
```
#!/bin/bash

read message

len=${#message}
line="${message//?/-}"

echo "+-${line}-+"
echo "| ${message} |"
echo "+-${line}-+"
```
```
./banner
hello
```
<img width="618" height="99" alt="3" src="https://github.com/user-attachments/assets/bab4dfe0-5a5a-488b-af8e-c68da0c8e478" />



## Задача 4
Написать программу для вывода всех идентификаторов (по правилам C/C++ или Java) в файле (без повторений).  
```
grep -o -E '[a-zA-Z_][a-zA-Z0-9_]*' helloworld.cpp | sort -u | tr '\n' ' '
```
<img width="689" height="40" alt="4" src="https://github.com/user-attachments/assets/ab4e21f5-36bd-4f11-9760-d51d8549d6ce" />



## Задача 5
Написать программу для регистрации пользовательской команды (правильные права доступа и копирование в /usr/local/bin).
```
nano reg
```
```
#!/bin/bash

read file
chmod 755 $file
sudo cp $file /usr/local/bin
```
```
chmod +x reg
./reg
banner
```
<img width="608" height="157" alt="6" src="https://github.com/user-attachments/assets/eeb732c0-e9aa-4697-9896-2242c5975be8" />



## Задача 6
Написать программу для проверки наличия комментария в первой строке файлов с расширением c, js и py.
```
nano findcomment
```
```
#!/bin/bash

file="helloworld.py"
line=$(head -n 1 "$file")

if [[ $line == "#"* || $line == "//"* || $line == "/*"* ]]; then
    echo "Комментарий есть"
else
    echo "Комментария нет"
fi
```
```
./findcomment
```
<img width="617" height="47" alt="image" src="https://github.com/user-attachments/assets/ad2ad758-2943-42cb-965d-cd734febfd90" />



## Задача 7
Написать программу для нахождения файлов-дубликатов (имеющих 1 или более копий содержимого) по заданному пути (и подкаталогам).  
```
#!/bin/bash

path="$1"

find "$path" -type f -exec sha256sum {} + > hashes.txt

awk 'NR == FNR { count[$1]++; next } count[$1] > 1' hashes.txt hashes.txt | sort
```
<img width="589" height="45" alt="image" src="https://github.com/user-attachments/assets/2f902348-b66b-4d4c-8d9c-907d53ac44d1" />



## Задача 8
Написать программу, которая находит все файлы в данном каталоге с расширением, указанным в качестве аргумента и архивирует все эти файлы в архив tar.  
```
#!/bin/bash

extension="$1"

find . -type f -name "*.$extension" -print0 | tar -cvf archive.tar --null -T -
```
<img width="319" height="76" alt="image" src="https://github.com/user-attachments/assets/f50eafbc-24b9-4fb1-9821-8612524e431c" />



## Задача 9
Написать программу, которая заменяет в файле последовательности из 4 пробелов на символ табуляции. Входной и выходной файлы задаются аргументами.  
```
#!/bin/bash

file="$1"
outp="$2"

sed $'s/    /\t/g' "$file" > "$outp"
```



## Задача 10
Написать программу, которая выводит названия всех пустых текстовых файлов в указанной директории. Директория передается в программу параметром.  
```
#!/bin/bash

path="$1"

find "$path" -type f -empty
```
<img width="423" height="156" alt="image" src="https://github.com/user-attachments/assets/c6e157c3-b127-4178-ae80-485c1dc2fd37" />
