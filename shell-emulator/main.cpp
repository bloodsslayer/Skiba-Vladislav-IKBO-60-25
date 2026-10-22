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
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
using namespace std;

Fl_Double_Window* win;
Fl_Text_Display* disp;
Fl_Text_Buffer* buf;
Fl_Input* input;

// Узел VFS: папка (JSON-объект) или файл (JSON-строка, данные в base64)
struct Node {
    bool isDir;
    map<string, Node> kids;
    string data;
};

Node root{true};
vector<string> cwd;  // текущий путь от корня
string vfsName = "default";

// Вывод строки в окно (и в консоль)
void print(const string& s) {
    buf->append((s + "\n").c_str());
    disp->insert_position(buf->length());
    disp->show_insert_position();
    cout << s << endl;
}

string pathStr(const vector<string>& p) {
    string s;
    for (auto& x : p) s += "/" + x;
    return s.empty() ? "/" : s;
}

string prompt() { return "user@" + vfsName + ":" + pathStr(cwd) + "$ "; }

// Мини-парсер JSON: поддерживает только объекты (папки) и строки (файлы)
struct JsonParser {
    const string& s;
    size_t i = 0;

    char peek() {
        while (i < s.size() && isspace((unsigned char)s[i])) i++;
        if (i >= s.size()) throw runtime_error("unexpected end of JSON");
        return s[i];
    }
    void expect(char c) {
        if (peek() != c) throw runtime_error(string("expected '") + c + "' at position " + to_string(i));
        i++;
    }
    string str() {
        expect('"');
        string r;
        while (i < s.size() && s[i] != '"') {
            if (s[i] == '\\') i++;
            if (i < s.size()) r += s[i++];
        }
        expect('"');
        return r;
    }
    Node value() {
        if (peek() == '"') return Node{false, {}, str()};
        expect('{');
        Node dir{true};
        if (peek() == '}') {
            i++;
            return dir;
        }
        while (true) {
            string name = str();
            expect(':');
            dir.kids[name] = value();
            if (peek() == ',') i++;
            else break;
        }
        expect('}');
        return dir;
    }
};

// Загрузка VFS из JSON-файла в память
void loadVfs(const string& path) {
    ifstream f(path);
    if (!f) {
        print("error: cannot open VFS: " + path);
        return;
    }
    string text((istreambuf_iterator<char>(f)), istreambuf_iterator<char>());
    try {
        JsonParser p{text};
        Node n = p.value();
        if (!n.isDir) throw runtime_error("root must be an object");
        root = n;
        vfsName = path.substr(path.find_last_of('/') + 1);
        vfsName = vfsName.substr(0, vfsName.rfind('.'));
    } catch (exception& e) {
        print("error: bad VFS file: " + string(e.what()));
    }
}

// Поиск узла по пути (абсолютному или относительному); nullptr, если не найден
Node* resolve(const string& path, vector<string>& result) {
    result = (!path.empty() && path[0] == '/') ? vector<string>() : cwd;
    size_t start = 0;
    while (start <= path.size()) {
        size_t end = path.find('/', start);
        if (end == string::npos) end = path.size();
        string part = path.substr(start, end - start);
        if (part == "..") {
            if (!result.empty()) result.pop_back();
        } else if (!part.empty() && part != ".") {
            result.push_back(part);
        }
        start = end + 1;
    }
    Node* n = &root;
    for (auto& name : result) {
        if (!n->isDir || !n->kids.count(name)) return nullptr;
        n = &n->kids[name];
    }
    return n;
}

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
        if (a.size() > 2) {
            print(a[0] + ": too many arguments");
            return false;
        }
        string path = a.size() == 2 ? a[1] : (a[0] == "ls" ? "." : "/");
        vector<string> p;
        Node* n = resolve(path, p);
        if (!n) {
            print(a[0] + ": no such file or directory: " + path);
            return false;
        }
        if (a[0] == "cd") {
            if (!n->isDir) {
                print("cd: not a directory: " + path);
                return false;
            }
            cwd = p;
        } else if (!n->isDir) {
            print(p.back());
        } else {
            for (auto& [name, kid] : n->kids) print(kid.isDir ? name + "/" : name);
        }
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
        if (!execute(line)) print("[script] error at line " + to_string(n));
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

    if (!vfsPath.empty()) loadVfs(vfsPath);
    win->copy_label(("Shell emulator - VFS: " + vfsName).c_str());
    win->show();
    if (!scriptPath.empty()) runScript(scriptPath);
    input->take_focus();
    return Fl::run();
}
