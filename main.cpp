// Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).
// Вариант 26.
#include <fstream>
#include <cstdio>
#include <iostream>
#include <map>
#include <sstream>
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
                graph[current].push_back(dep);
            }
        }
    }
    return graph;
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

    string text = download(config.repo);
    if (text.empty()) {
        cerr << "Error: cannot download repository: " << config.repo
             << "\n";
        return 1;
    }
    Graph graph = parse_packages(text);
    if (graph.count(config.package) == 0) {
        cerr << "Error: package not found: " << config.package << "\n";
        return 1;
    }

    cout << "Direct dependencies of " << config.package << ":\n";
    for (const string &dep : graph[config.package]) {
        cout << "  " << dep << "\n";
    }
    return 0;
}
