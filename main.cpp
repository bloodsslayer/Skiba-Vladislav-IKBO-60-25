// Инструмент визуализации графа зависимостей пакетов Ubuntu (apt).
// Вариант 26.
#include <fstream>
#include <iostream>
#include <string>

using namespace std;

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

int main(int argc, char *argv[])
{
    Config config;
    string error = parse_args(argc, argv, config);
    if (!error.empty()) {
        cerr << "Error: " << error << "\n";
        print_usage();
        return 1;
    }

    cout << "package=" << config.package << "\n";
    cout << "repo=" << config.repo << "\n";
    cout << "test_mode=" << (config.test_mode ? "true" : "false") << "\n";
    cout << "ascii_tree=" << (config.ascii_tree ? "true" : "false")
         << "\n";
    cout << "filter=" << config.filter << "\n";
    return 0;
}
