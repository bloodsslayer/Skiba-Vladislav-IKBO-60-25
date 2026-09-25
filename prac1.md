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
