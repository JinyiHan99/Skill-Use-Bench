"""Tests for the calculator module."""
import pytest
from src.calculator import Calculator


@pytest.fixture
def calc():
    return Calculator()


def test_add_positive_numbers(calc):
    assert calc.add(2, 3) == 5


def test_add_negative_numbers(calc):
    assert calc.add(-1, -1) == -2


def test_subtract_basic(calc):
    assert calc.subtract(10, 4) == 6


def test_multiply_basic(calc):
    assert calc.multiply(3, 7) == 21


def test_multiply_by_zero(calc):
    assert calc.multiply(5, 0) == 0


def test_power_basic(calc):
    assert calc.power(2, 3) == 8


def test_history_records_operations(calc):
    calc.add(1, 2)
    calc.multiply(3, 4)
    history = calc.get_history()
    assert len(history) == 2
    assert history[0][0] == "add"
    assert history[1][0] == "multiply"


def test_clear_history(calc):
    calc.add(1, 1)
    calc.clear_history()
    assert calc.get_history() == []
