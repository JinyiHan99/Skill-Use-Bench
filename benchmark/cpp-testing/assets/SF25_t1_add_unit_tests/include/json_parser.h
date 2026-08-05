#pragma once

#include <string>
#include <variant>
#include <vector>
#include <unordered_map>
#include <stdexcept>

namespace json {

class ParseError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class Value;
using Object = std::unordered_map<std::string, Value>;
using Array = std::vector<Value>;

class Value {
public:
    using Variant = std::variant<std::nullptr_t, bool, double, std::string, Array, Object>;

    Value() : data_(nullptr) {}
    explicit Value(std::nullptr_t) : data_(nullptr) {}
    explicit Value(bool b) : data_(b) {}
    explicit Value(double d) : data_(d) {}
    explicit Value(const std::string& s) : data_(s) {}
    explicit Value(std::string&& s) : data_(std::move(s)) {}
    explicit Value(const Array& a) : data_(a) {}
    explicit Value(Array&& a) : data_(std::move(a)) {}
    explicit Value(const Object& o) : data_(o) {}
    explicit Value(Object&& o) : data_(std::move(o)) {}

    bool is_null() const { return std::holds_alternative<std::nullptr_t>(data_); }
    bool is_bool() const { return std::holds_alternative<bool>(data_); }
    bool is_number() const { return std::holds_alternative<double>(data_); }
    bool is_string() const { return std::holds_alternative<std::string>(data_); }
    bool is_array() const { return std::holds_alternative<Array>(data_); }
    bool is_object() const { return std::holds_alternative<Object>(data_); }

    bool as_bool() const { return std::get<bool>(data_); }
    double as_number() const { return std::get<double>(data_); }
    const std::string& as_string() const { return std::get<std::string>(data_); }
    const Array& as_array() const { return std::get<Array>(data_); }
    const Object& as_object() const { return std::get<Object>(data_); }

private:
    Variant data_;
};

// Parse a JSON string into a Value. Throws ParseError on invalid input.
Value parse(const std::string& input);

// Serialize a Value back to a JSON string.
std::string serialize(const Value& value);

} // namespace json
