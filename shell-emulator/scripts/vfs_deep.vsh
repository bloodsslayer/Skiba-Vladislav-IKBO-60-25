# VFS с вложенностью 6 уровней; стартовый каталог - домашний (~).
ls
cd docs/reports/2024        # относительный путь через 3 уровня
ls -l
cd ../2025                  # переход через ..
ls
cd /home/user/projects/emulator/src    # абсолютный путь
ls -l main.py
cd -                        # возврат в предыдущий каталог
cd                          # без аргумента - домой
ls -a
ls / /etc ~/docs            # несколько каталогов сразу
cd /var/log/syslog          # ошибка: не каталог
cd /home/user/docs/reports/2024/q1.txt/x   # ошибка: q1.txt не каталог
