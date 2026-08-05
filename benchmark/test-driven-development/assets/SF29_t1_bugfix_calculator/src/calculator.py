"""Simple calculator module for arithmetic operations."""


class Calculator:
    """A basic calculator that supports standard arithmetic operations."""

    def __init__(self, precision: int = 2):
        self._precision = precision
        self._history = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = round(a + b, self._precision)
        self._history.append(("add", a, b, result))
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        result = round(a - b, self._precision)
        self._history.append(("subtract", a, b, result))
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = round(a * b, self._precision)
        self._history.append(("multiply", a, b, result))
        return result

    def divide(self, a: float, b: float) -> float:
        """Divide a by b."""
        result = round(a / b, self._precision)
        self._history.append(("divide", a, b, result))
        return result

    def power(self, base: float, exponent: float) -> float:
        """Raise base to the power of exponent."""
        result = round(base ** exponent, self._precision)
        self._history.append(("power", base, exponent, result))
        return result

    def get_history(self) -> list:
        """Return the history of operations."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear the operation history."""
        self._history.clear()
