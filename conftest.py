import pytest  # noqa: D100


@pytest.fixture
def some_func():
    """Some function."""

    def func(str_1: str, int_1: int):
        return str_1 + str(int_1)

    return func
