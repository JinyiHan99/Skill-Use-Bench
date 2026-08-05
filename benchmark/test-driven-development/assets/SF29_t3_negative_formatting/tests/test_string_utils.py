"""Tests for string utility functions — full coverage."""
import pytest
from src.string_utils import (
    capitalize_words,
    truncate,
    snake_to_camel,
    camel_to_snake,
    count_vowels,
    reverse_words,
)


def test_capitalize_words_basic():
    assert capitalize_words("hello world") == "Hello World"


def test_capitalize_words_single():
    assert capitalize_words("hello") == "Hello"


def test_truncate_short_text():
    assert truncate("hi", 10) == "hi"


def test_truncate_long_text():
    assert truncate("hello world", 8) == "hello..."


def test_truncate_custom_suffix():
    assert truncate("hello world", 8, suffix="~") == "hello w~"


def test_snake_to_camel_basic():
    assert snake_to_camel("hello_world") == "helloWorld"


def test_snake_to_camel_single():
    assert snake_to_camel("hello") == "hello"


def test_camel_to_snake_basic():
    assert camel_to_snake("helloWorld") == "hello_world"


def test_camel_to_snake_single():
    assert camel_to_snake("hello") == "hello"


def test_count_vowels_basic():
    assert count_vowels("hello") == 2


def test_count_vowels_no_vowels():
    assert count_vowels("xyz") == 0


def test_reverse_words_basic():
    assert reverse_words("hello world foo") == "foo world hello"


def test_reverse_words_single():
    assert reverse_words("hello") == "hello"
