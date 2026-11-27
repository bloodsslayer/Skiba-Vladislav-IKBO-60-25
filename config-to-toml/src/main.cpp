#include <deque>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <variant>

struct Value;
using Table = std::map<std::string, const Value*>;

struct Value {
    std::variant<std::string, Table> data;
};

static std::string normalizeNumber(const std::string& text) {
    auto normalized = text;
    const std::size_t start = text[0] == '+' || text[0] == '-' ? 1 : 0;
    const auto firstNonzero = text.find_first_not_of('0', start);
    const auto keepFrom = text[firstNonzero] == '.' && firstNonzero > start
                              ? firstNonzero - 1 : firstNonzero;
    normalized.erase(start, keepFrom - start);
    return normalized;
}

static std::string quoteString(const std::string& text) {
    const char hex[] = "0123456789ABCDEF";
    std::string escaped = "\"";
    for (const unsigned char ch : text) {
        if (ch == '\\') {
            escaped += "\\\\";
        } else if (ch < 0x20 || ch == 0x7F) {
            escaped += "\\u00";
            escaped += hex[ch >> 4];
            escaped += hex[ch & 0x0F];
        } else {
            escaped += static_cast<char>(ch);
        }
    }
    escaped += '"';
    return escaped;
}

class Parser {
public:
    explicit Parser(std::string_view input) : input(input) {}

    const Table& parse() {
        while (consume("(")) {
            parseDefinition();
        }

        const auto start = cursor;
        const auto& value = parseValue();
        const auto* table = std::get_if<Table>(&value.data);
        if (!table) {
            fail(start, "Корневое значение должно быть словарём");
        }
        skipSpace();
        if (cursor != input.size()) {
            fail(cursor, "Лишний текст после корневого словаря");
        }
        return *table;
    }

private:
    std::string_view input;
    std::size_t cursor = 0;
    std::deque<Value> values;
    Table constants;

    [[noreturn]] void fail(std::size_t position, const std::string& message) const {
        std::size_t line = 1;
        std::size_t column = 1;
        for (std::size_t i = 0; i < position; ++i) {
            if (input[i] == '\n') {
                ++line;
                column = 1;
            } else {
                ++column;
            }
        }
        throw std::runtime_error(
            "Ошибка (" + std::to_string(line) + ":" + std::to_string(column) + "): " + message);
    }

    void skipSpace() {
        readRun(" \t\r\n");
    }

    bool consume(std::string_view token) {
        skipSpace();
        if (input.substr(cursor, token.size()) != token) {
            return false;
        }
        cursor += token.size();
        return true;
    }

    void expect(std::string_view token) {
        if (!consume(token)) {
            fail(cursor, "Ожидалось «" + std::string(token) + "»");
        }
    }

    void readRun(std::string_view allowed) {
        const auto end = input.find_first_not_of(allowed, cursor);
        cursor = end == std::string_view::npos ? input.size() : end;
    }

    std::string readName() {
        const auto start = cursor;
        readRun("abcdefghijklmnopqrstuvwxyz");
        if (cursor == start) {
            fail(start, "Ожидалось имя из строчных латинских букв");
        }
        return std::string(input.substr(start, cursor - start));
    }

    const Value& store(Value value) {
        values.push_back(std::move(value));
        return values.back();
    }

    void parseDefinition() {
        skipSpace();
        const auto keyword = cursor;
        if (readName() != "def") {
            fail(keyword, "Ожидалось слово def");
        }
        skipSpace();
        const auto start = cursor;
        const auto name = readName();
        const auto& value = parseValue();
        expect(")");
        if (!constants.emplace(name, &value).second) {
            fail(start, "Константа уже объявлена: " + name);
        }
    }

    const Value& parseValue() {
        skipSpace();
        if (cursor == input.size()) {
            fail(cursor, "Ожидалось значение");
        }

        const auto start = cursor;
        const char ch = input[cursor];
        if (ch == '@') return parseString();
        if (ch == '$') return parseReference();
        if ((ch >= '0' && ch <= '9') || ch == '+' || ch == '-') return parseNumber();
        if (ch >= 'a' && ch <= 'z' && readName() == "table") return parseTable();
        fail(start, "Ожидалось число, строка, словарь или ссылка на константу");
    }

    const Value& parseTable() {
        expect("(");
        Table fields;
        while (!consume(")")) {
            const auto start = cursor;
            const auto name = readName();
            expect("=>");
            const auto& value = parseValue();
            if (!fields.emplace(name, &value).second) {
                fail(start, "Повторяющийся ключ: " + name);
            }
            if (!consume(",")) {
                expect(")");
                break;
            }
        }
        return store({std::move(fields)});
    }

    const Value& parseNumber() {
        const auto start = cursor;
        if (input[cursor] == '+' || input[cursor] == '-') ++cursor;
        const auto integerStart = cursor;
        readRun("0123456789");
        if (cursor == integerStart || cursor == input.size() || input[cursor] != '.') {
            fail(start, "Ожидалось число вида 0.0");
        }
        const auto fractionStart = ++cursor;
        readRun("0123456789");
        if (cursor == fractionStart) {
            fail(start, "Ожидалась дробная часть числа");
        }
        return store({normalizeNumber(std::string(input.substr(start, cursor - start)))});
    }

    const Value& parseString() {
        const auto start = cursor;
        if (input.substr(cursor, 2) != "@\"") {
            fail(start, "Строка должна начинаться с @\"");
        }
        const auto end = input.find('"', cursor + 2);
        if (end == std::string_view::npos) {
            fail(start, "Незакрытая строка");
        }
        cursor = end + 1;
        return store({quoteString(std::string(input.substr(start + 2, end - start - 2)))});
    }

    const Value& parseReference() {
        const auto start = cursor++;
        const auto name = readName();
        if (cursor == input.size() || input[cursor] != '$') {
            fail(start, "Ожидалась ссылка вида $имя$");
        }
        ++cursor;
        const auto found = constants.find(name);
        if (found == constants.end()) {
            fail(start, "Неизвестная константа: " + name);
        }
        return *found->second;
    }
};

static void writeValue(std::ostream& output, const Value& value) {
    if (const auto* text = std::get_if<std::string>(&value.data)) {
        output << *text;
        return;
    }

    output << '{';
    bool first = true;
    for (const auto& [name, field] : std::get<Table>(value.data)) {
        if (!first) output << ", ";
        output << name << " = ";
        writeValue(output, *field);
        first = false;
    }
    output << '}';
}

static void writeToml(const char* path, const Table& root) {
    std::ofstream output(path, std::ios::binary);
    if (!output) {
        throw std::runtime_error(std::string("Не удалось открыть файл: ") + path);
    }
    for (const auto& [name, value] : root) {
        output << name << " = ";
        writeValue(output, *value);
        output << '\n';
    }
    output.close();
    if (!output) {
        throw std::runtime_error(std::string("Не удалось записать файл: ") + path);
    }
}

int main(int argc, char** argv) {
    if (argc != 3 || std::string(argv[1]) != "-o" || argv[2][0] == '\0') {
        std::cerr << "Использование: " << argv[0] << " -o <путь к TOML-файлу>\n";
        return 2;
    }

    try {
        const std::string input{std::istreambuf_iterator<char>(std::cin), {}};
        Parser parser(input);
        writeToml(argv[2], parser.parse());
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
