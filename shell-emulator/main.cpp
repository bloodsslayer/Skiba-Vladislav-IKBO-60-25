// Эмулятор командной оболочки UNIX (вариант 26)
// Сборка: ./build.sh

#include <FL/Fl.H>
#include <FL/Fl_Double_Window.H>
#include <FL/Fl_Input.H>
#include <FL/Fl_Text_Display.H>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
using namespace std;

Fl_Double_Window* win;
Fl_Text_Display* disp;
Fl_Text_Buffer* buf;
Fl_Input* input;

string vfsName = "default";

// Вывод строки в окно (и в консоль)
void print(const string& s) {
    buf->append((s + "\n").c_str());
    disp->insert_position(buf->length());
    disp->show_insert_position();
    cout << s << endl;
}

string prompt() { return "user@" + vfsName + ":~$ "; }

// Разбор строки на аргументы с поддержкой кавычек '...' и "..."
bool parse(const string& line, vector<string>& args, string& err) {
    string cur;
    bool has = false;
    char quote = 0;
    for (char c : line) {
        if (quote) {
            if (c == quote) quote = 0;
            else cur += c;
        } else if (c == '"' || c == '\'') {
            quote = c;
            has = true;
        } else if (isspace((unsigned char)c)) {
            if (has) args.push_back(cur);
            cur.clear();
            has = false;
        } else {
            cur += c;
            has = true;
        }
    }
    if (quote) {
        err = "parse error: unterminated quote";
        return false;
    }
    if (has) args.push_back(cur);
    return true;
}

// Выполнение одной команды; возвращает false при ошибке
bool execute(const string& line) {
    print(prompt() + line);
    vector<string> a;
    string err;
    if (!parse(line, a, err)) {
        print(err);
        return false;
    }
    if (a.empty()) return true;

    if (a[0] == "ls" || a[0] == "cd") {
        string s = a[0] + ": args =";
        for (size_t i = 1; i < a.size(); i++) s += " [" + a[i] + "]";
        print(s);
        return true;
    }
    if (a[0] == "exit") {
        if (a.size() > 2) {
            print("exit: too many arguments");
            return false;
        }
        exit(a.size() == 2 ? atoi(a[1].c_str()) : 0);
    }
    print(a[0] + ": command not found");
    return false;
}

// Выполнение стартового скрипта; строки, начинающиеся с //, - комментарии
void runScript(const string& path) {
    ifstream f(path);
    if (!f) {
        print("error: cannot open script: " + path);
        return;
    }
    string line;
    int n = 0;
    while (getline(f, line)) {
        n++;
        size_t p = line.find_first_not_of(" \t\r");
        if (p == string::npos || line.compare(p, 2, "//") == 0) continue;
        if (line.back() == '\r') line.pop_back();
        if (!execute(line)) {
            print("script stopped: error at line " + to_string(n));
            return;
        }
    }
}

void onEnter(Fl_Widget*, void*) {
    string line = input->value();
    input->value("");
    execute(line);
}

int main(int argc, char** argv) {
    string vfsPath, scriptPath;
    for (int i = 1; i < argc; i++) {
        string a = argv[i];
        if (a == "--vfs" && i + 1 < argc) vfsPath = argv[++i];
        else if (a == "--script" && i + 1 < argc) scriptPath = argv[++i];
        else {
            cerr << "error: bad argument '" << a << "'\n"
                 << "usage: emulator [--vfs <path>] [--script <path>]\n";
            return 1;
        }
    }

    win = new Fl_Double_Window(800, 500);
    buf = new Fl_Text_Buffer();
    disp = new Fl_Text_Display(5, 5, 790, 455);
    disp->buffer(buf);
    disp->textfont(FL_COURIER);
    input = new Fl_Input(5, 465, 790, 30);
    input->textfont(FL_COURIER);
    input->when(FL_WHEN_ENTER_KEY_ALWAYS);
    input->callback(onEnter);
    win->resizable(disp);
    win->end();

    // Отладочный вывод параметров
    print("[debug] vfs path    = " + (vfsPath.empty() ? "(not set)" : vfsPath));
    print("[debug] script path = " + (scriptPath.empty() ? "(not set)" : scriptPath));

    win->copy_label(("Shell emulator - VFS: " + vfsName).c_str());
    win->show();
    if (!scriptPath.empty()) runScript(scriptPath);
    input->take_focus();
    return Fl::run();
}
