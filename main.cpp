// Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).
// Вариант 26.
#include <fstream>
#include <algorithm>
#include <cstdio>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

using Graph = map<string, vector<string>>;

struct Config {
    string package;
    string repo;
    bool test_mode = false;
    bool ascii_tree = false;
    string filter;
};

void print_usage()
{
    cout << "Usage: depviz --package NAME --repo URL_OR_PATH"
         << " [--test-mode] [--ascii-tree] [--filter SUBSTRING]\n";
}

// Разбирает аргументы командной строки. Возвращает текст ошибки
// или пустую строку, если всё в порядке.
string parse_args(int argc, char *argv[], Config &config)
{
    for (int i = 1; i < argc; i++) {
        string arg = argv[i];
        if (arg == "--test-mode") {
            config.test_mode = true;
        } else if (arg == "--ascii-tree") {
            config.ascii_tree = true;
        } else if (arg == "--package" || arg == "--repo"
                   || arg == "--filter") {
            if (i + 1 >= argc) {
                return "option " + arg + " requires a value";
            }
            string value = argv[++i];
            if (value.empty()) {
                return "option " + arg + " must not be empty";
            }
            if (arg == "--package") {
                config.package = value;
            } else if (arg == "--repo") {
                config.repo = value;
            } else {
                config.filter = value;
            }
        } else {
            return "unknown option: " + arg;
        }
    }

    if (config.package.empty()) {
        return "package name is required (--package)";
    }
    if (config.package.find_first_of(" \t'\"") != string::npos) {
        return "invalid package name: " + config.package;
    }
    if (config.repo.empty()) {
        return "repository is required (--repo)";
    }
    if (config.test_mode) {
        ifstream file(config.repo);
        if (!file) {
            return "cannot open test repository file: " + config.repo;
        }
    } else {
        bool is_url = config.repo.rfind("http://", 0) == 0
                      || config.repo.rfind("https://", 0) == 0;
        if (!is_url) {
            return "repository must be an http(s) URL: " + config.repo;
        }
        if (config.repo.find('\'') != string::npos) {
            return "invalid character in URL: " + config.repo;
        }
    }
    return "";
}

string trim(const string &text)
{
    size_t begin = text.find_first_not_of(" \t\r\n");
    if (begin == string::npos) {
        return "";
    }
    size_t end = text.find_last_not_of(" \t\r\n");
    return text.substr(begin, end - begin + 1);
}

// Скачивает файл Packages (или Packages.gz) по URL через curl.
string download(const string &url)
{
    string command = "curl -sfL '" + url + "'";
    if (url.size() > 3 && url.substr(url.size() - 3) == ".gz") {
        command += " | gunzip";
    }
    FILE *pipe = popen(command.c_str(), "r");
    if (pipe == nullptr) {
        return "";
    }
    string result;
    char buffer[65536];
    size_t count;
    while ((count = fread(buffer, 1, sizeof(buffer), pipe)) > 0) {
        result.append(buffer, count);
    }
    pclose(pipe);
    return result;
}

// Разбирает строку "a (>= 1), b | c, d:any" в список имён [a, b, d].
// Из альтернатив "b | c" берётся первая, версии и архитектуры
// отбрасываются.
vector<string> parse_depends(const string &line)
{
    vector<string> result;
    stringstream stream(line);
    string item;
    while (getline(stream, item, ',')) {
        item = item.substr(0, item.find('|'));
        item = item.substr(0, item.find('('));
        item = item.substr(0, item.find(':'));
        item = trim(item);
        if (!item.empty()) {
            result.push_back(item);
        }
    }
    return result;
}

// Добавляет ребро from -> to, если его ещё нет.
void add_edge(Graph &graph, const string &from, const string &to)
{
    vector<string> &deps = graph[from];
    if (find(deps.begin(), deps.end(), to) == deps.end()) {
        deps.push_back(to);
    }
}

// Разбирает индекс пакетов apt: имя пакета -> прямые зависимости.
Graph parse_packages(const string &text)
{
    Graph graph;
    stringstream stream(text);
    string line;
    string current;
    while (getline(stream, line)) {
        if (line.rfind("Package:", 0) == 0) {
            current = trim(line.substr(8));
            graph[current];
        } else if (line.rfind("Depends:", 0) == 0
                   || line.rfind("Pre-Depends:", 0) == 0) {
            string value = line.substr(line.find(':') + 1);
            for (const string &dep : parse_depends(value)) {
                add_edge(graph, current, dep);
            }
        }
    }
    return graph;
}

bool is_test_name(const string &name)
{
    if (name.empty()) {
        return false;
    }
    for (char c : name) {
        if (c < 'A' || c > 'Z') {
            return false;
        }
    }
    return true;
}

// Разбирает тестовый репозиторий: строки вида "A: B C".
// Пакеты называются большими латинскими буквами, # - комментарий.
Graph parse_test_repo(const string &text)
{
    Graph graph;
    stringstream stream(text);
    string line;
    int number = 0;
    while (getline(stream, line)) {
        number++;
        line = trim(line.substr(0, line.find('#')));
        if (line.empty()) {
            continue;
        }
        size_t colon = line.find(':');
        string name = trim(line.substr(0, colon));
        if (colon == string::npos || !is_test_name(name)) {
            throw runtime_error("bad line " + to_string(number)
                                + " in test repository: " + line);
        }
        graph[name];
        stringstream deps(line.substr(colon + 1));
        string dep;
        while (deps >> dep) {
            if (!is_test_name(dep)) {
                throw runtime_error("bad package name '" + dep
                                    + "' on line " + to_string(number));
            }
            add_edge(graph, name, dep);
        }
    }
    return graph;
}

Graph load_repo(const Config &config)
{
    if (config.test_mode) {
        ifstream file(config.repo);
        stringstream text;
        text << file.rdbuf();
        return parse_test_repo(text.str());
    }
    string text = download(config.repo);
    if (text.empty()) {
        throw runtime_error("cannot download repository: " + config.repo);
    }
    return parse_packages(text);
}

bool is_filtered(const string &name, const string &filter)
{
    return !filter.empty() && name.find(filter) != string::npos;
}

// Строит граф всех (транзитивных) зависимостей пакета start обходом
// в глубину без рекурсии. Пакеты, содержащие filter, пропускаются.
// Обратные рёбра (циклы) записываются в cycles.
Graph build_graph(const Graph &repo, const string &start,
                  const string &filter, vector<string> &cycles)
{
    const vector<string> no_deps;
    Graph result;
    map<string, int> state;  // 0 - не посещён, 1 - в стеке, 2 - готов
    vector<pair<string, size_t>> stack;

    result[start];
    state[start] = 1;
    stack.push_back({start, 0});
    while (!stack.empty()) {
        string name = stack.back().first;
        size_t index = stack.back().second;
        auto found = repo.find(name);
        const vector<string> &deps =
            found == repo.end() ? no_deps : found->second;
        if (index >= deps.size()) {
            state[name] = 2;
            stack.pop_back();
            continue;
        }
        stack.back().second++;

        const string &dep = deps[index];
        if (is_filtered(dep, filter)) {
            continue;
        }
        result[name].push_back(dep);
        if (state[dep] == 1) {
            cycles.push_back(name + " -> " + dep);
        } else if (state[dep] == 0) {
            state[dep] = 1;
            result[dep];
            stack.push_back({dep, 0});
        }
    }
    return result;
}

int main(int argc, char *argv[])
{
    Config config;
    string error = parse_args(argc, argv, config);
    if (!error.empty()) {
        cerr << "Error: " << error << "\n";
        print_usage();
        return 1;
    }

    try {
        Graph repo = load_repo(config);
        if (repo.count(config.package) == 0) {
            throw runtime_error("package not found: " + config.package);
        }
        if (is_filtered(config.package, config.filter)) {
            throw runtime_error("package itself matches the filter");
        }
        vector<string> cycles;
        Graph graph = build_graph(repo, config.package, config.filter,
                                  cycles);

        cout << "Dependency graph of " << config.package << ":\n";
        for (const auto &node : graph) {
            cout << "  " << node.first << ":";
            for (const string &dep : node.second) {
                cout << " " << dep;
            }
            cout << "\n";
        }
        for (const string &cycle : cycles) {
            cout << "Cycle detected: " << cycle << "\n";
        }
    } catch (const exception &e) {
        cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
