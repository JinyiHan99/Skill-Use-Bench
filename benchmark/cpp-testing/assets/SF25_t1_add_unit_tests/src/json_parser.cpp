#include "json_parser.h"
#include <cctype>
#include <sstream>
#include <cmath>

namespace json {

namespace {

class Parser {
public:
    explicit Parser(const std::string& input) : input_(input), pos_(0) {}

    Value parse_value() {
        skip_whitespace();
        if (pos_ >= input_.size()) {
            throw ParseError("Unexpected end of input");
        }

        char c = input_[pos_];
        if (c == '"') return parse_string_value();
        if (c == '{') return parse_object();
        if (c == '[') return parse_array();
        if (c == 't' || c == 'f') return parse_bool();
        if (c == 'n') return parse_null();
        if (c == '-' || std::isdigit(c)) return parse_number();

        throw ParseError(std::string("Unexpected character: ") + c);
    }

private:
    void skip_whitespace() {
        while (pos_ < input_.size() && std::isspace(input_[pos_])) {
            ++pos_;
        }
    }

    char peek() const {
        if (pos_ >= input_.size()) throw ParseError("Unexpected end of input");
        return input_[pos_];
    }

    char advance() {
        if (pos_ >= input_.size()) throw ParseError("Unexpected end of input");
        return input_[pos_++];
    }

    void expect(char c) {
        skip_whitespace();
        if (advance() != c) {
            throw ParseError(std::string("Expected '") + c + "'");
        }
    }

    Value parse_null() {
        if (input_.substr(pos_, 4) == "null") {
            pos_ += 4;
            return Value(nullptr);
        }
        throw ParseError("Invalid null literal");
    }

    Value parse_bool() {
        if (input_.substr(pos_, 4) == "true") {
            pos_ += 4;
            return Value(true);
        }
        if (input_.substr(pos_, 5) == "false") {
            pos_ += 5;
            return Value(false);
        }
        throw ParseError("Invalid boolean literal");
    }

    Value parse_number() {
        size_t start = pos_;
        if (input_[pos_] == '-') ++pos_;

        if (pos_ < input_.size() && input_[pos_] == '0') {
            ++pos_;
        } else {
            while (pos_ < input_.size() && std::isdigit(input_[pos_])) ++pos_;
        }

        if (pos_ < input_.size() && input_[pos_] == '.') {
            ++pos_;
            while (pos_ < input_.size() && std::isdigit(input_[pos_])) ++pos_;
        }

        if (pos_ < input_.size() && (input_[pos_] == 'e' || input_[pos_] == 'E')) {
            ++pos_;
            if (pos_ < input_.size() && (input_[pos_] == '+' || input_[pos_] == '-')) ++pos_;
            while (pos_ < input_.size() && std::isdigit(input_[pos_])) ++pos_;
        }

        double val = std::stod(input_.substr(start, pos_ - start));
        return Value(val);
    }

    std::string parse_string() {
        expect('"');
        std::string result;
        while (pos_ < input_.size() && input_[pos_] != '"') {
            if (input_[pos_] == '\\') {
                ++pos_;
                if (pos_ >= input_.size()) throw ParseError("Unexpected end in string escape");
                switch (input_[pos_]) {
                    case '"': result += '"'; break;
                    case '\\': result += '\\'; break;
                    case '/': result += '/'; break;
                    case 'b': result += '\b'; break;
                    case 'f': result += '\f'; break;
                    case 'n': result += '\n'; break;
                    case 'r': result += '\r'; break;
                    case 't': result += '\t'; break;
                    default: throw ParseError("Invalid escape sequence");
                }
            } else {
                result += input_[pos_];
            }
            ++pos_;
        }
        if (pos_ >= input_.size()) throw ParseError("Unterminated string");
        ++pos_; // skip closing quote
        return result;
    }

    Value parse_string_value() {
        // Don't call expect('"') since parse_string does it
        std::string s = parse_string();
        return Value(std::move(s));
    }

    Value parse_array() {
        advance(); // skip '['
        skip_whitespace();
        Array arr;
        if (peek() == ']') {
            advance();
            return Value(std::move(arr));
        }
        while (true) {
            arr.push_back(parse_value());
            skip_whitespace();
            if (peek() == ']') {
                advance();
                return Value(std::move(arr));
            }
            expect(',');
        }
    }

    Value parse_object() {
        advance(); // skip '{'
        skip_whitespace();
        Object obj;
        if (peek() == '}') {
            advance();
            return Value(std::move(obj));
        }
        while (true) {
            skip_whitespace();
            std::string key = parse_string();
            expect(':');
            Value val = parse_value();
            obj[std::move(key)] = std::move(val);
            skip_whitespace();
            if (peek() == '}') {
                advance();
                return Value(std::move(obj));
            }
            expect(',');
        }
    }

    const std::string& input_;
    size_t pos_;
};

} // anonymous namespace

Value parse(const std::string& input) {
    Parser parser(input);
    Value result = parser.parse_value();
    return result;
}

std::string serialize(const Value& value) {
    if (value.is_null()) return "null";
    if (value.is_bool()) return value.as_bool() ? "true" : "false";
    if (value.is_number()) {
        double d = value.as_number();
        if (d == std::floor(d) && std::abs(d) < 1e15) {
            long long i = static_cast<long long>(d);
            return std::to_string(i);
        }
        std::ostringstream oss;
        oss << d;
        return oss.str();
    }
    if (value.is_string()) {
        std::string result = "\"";
        for (char c : value.as_string()) {
            switch (c) {
                case '"': result += "\\\""; break;
                case '\\': result += "\\\\"; break;
                case '\n': result += "\\n"; break;
                case '\t': result += "\\t"; break;
                case '\r': result += "\\r"; break;
                default: result += c;
            }
        }
        result += "\"";
        return result;
    }
    if (value.is_array()) {
        std::string result = "[";
        const auto& arr = value.as_array();
        for (size_t i = 0; i < arr.size(); ++i) {
            if (i > 0) result += ",";
            result += serialize(arr[i]);
        }
        result += "]";
        return result;
    }
    if (value.is_object()) {
        std::string result = "{";
        bool first = true;
        for (const auto& [k, v] : value.as_object()) {
            if (!first) result += ",";
            first = false;
            result += "\"" + k + "\":" + serialize(v);
        }
        result += "}";
        return result;
    }
    return "null";
}

} // namespace json
