from dataclasses import dataclass  # noqa: D100

import pytest  # noqa: D100


@pytest.fixture
def some_func():
    """Some function."""

    def func(str_1: str, int_1: int):
        return str_1 + str(int_1)

    return func


@pytest.fixture
def some_class():
    """Returns some class."""

    class Some:
        def __init__(self) -> None:
            pass

        def func(self, str_1: str, int_1: int):
            return str_1 + str(int_1)

    return Some


@pytest.fixture
def some_dataclass():
    """Returns some dataclass."""

    @dataclass
    class Some:
        def __init__(self) -> None:
            pass

        def func(self, str_1: str, int_1: int):
            return str_1 + str(int_1)

    return Some()
