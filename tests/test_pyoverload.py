from dataclasses import dataclass  # noqa: D100
from typing import get_type_hints

import pytest

from pyoverload.pyoverload import Function
from pyoverload.pyoverload import overload


def as_valid_key(dictionary):
    """Turns a dictionary into a tuple.

    First entry is a tuple containing the key, second entry is tuple containing the
    values. Required to create a hashable object of the type-hints of a function,
    that can used for a dictionary key.

    Args:
        dictionary (Dict[Any, Any]): Some dictionary.

    Returns:
        Tuple[tuple, tuple]: The tuple.
    """
    keys = tuple([key for key in dictionary.keys()])
    values = tuple([value for value in dictionary.values()])
    return (keys, values)


def test_function_init(some_func):
    """Test the `__init__`-method of `Function`.

    Args:
        some_func (Callable): Some function.
    """
    func = Function(some_func)
    expected = tuple(
        [
            some_func.__module__,
            some_func.__class__,
            some_func.__name__,
            as_valid_key(get_type_hints(some_func))
            # tuple(value for value in get_type_hints(some_func).values()),
            # frozenset(get_type_hints(some_func).items())
        ]
    )
    assert expected == func.key()


def test_overload():
    """Tests the overload decorator."""

    @dataclass
    class Some:
        text: str = "Hello"

    @overload
    def some_func(str_1: str, int_1: int):
        return str_1 + str(int_1)

    @overload
    def some_func(str_1: str):  # noqa: F811
        return str_1

    @overload
    def some_func(obj: Some):  # noqa: F811
        return obj.text

    kwargs = {"str_1": "Number: ", "int_1": 1}
    args = ["Number: ", 1]
    assert some_func(**kwargs) == "Number: 1"
    assert some_func(*args) == "Number: 1"
    assert some_func("cheese") == "cheese"
    assert some_func(str_1="cheese") == "cheese"
    with pytest.raises(TypeError) as excinfo:
        some_func(str_1=2)
    assert "'str_1' needs to be of type" in str(excinfo)
    with pytest.raises(TypeError) as excinfo:
        some_func(str_1="Number: ", int_1="1")
    assert "'int_1' needs to be of type" in str(excinfo)
    with pytest.raises(TypeError) as excinfo:
        some_func(obj=2)
    assert "'obj' needs to be of type" in str(excinfo)
    with pytest.raises(Exception) as excinfo:
        some_func(int_1=1)
    assert "No matching function found." in str(excinfo)
    assert some_func(int_1=1, str_1="Number: ") == "Number: 1"
    assert some_func(Some()) == "Hello"
    assert some_func(obj=Some()) == "Hello"
