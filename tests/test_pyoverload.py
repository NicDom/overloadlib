from dataclasses import dataclass  # noqa: D100
from typing import Any
from typing import Callable
from typing import Dict
from typing import get_type_hints
from typing import Tuple

import pytest

from pyoverload.pyoverload import _generate_key
from pyoverload.pyoverload import func_versions_info
from pyoverload.pyoverload import Function
from pyoverload.pyoverload import NamespaceKey
from pyoverload.pyoverload import NoFunctionFoundError
from pyoverload.pyoverload import overload


def as_valid_key(dictionary: Dict[Any, Any]) -> Tuple[Any, Any]:
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


def test_function_init(some_func: Callable[..., Any]) -> None:
    """Test the `__init__`-method of `Function`.

    Args:
        some_func (Callable): Some function.
    """
    func = Function(some_func)
    expected = NamespaceKey(
        some_func.__module__,
        some_func.__qualname__,
        some_func.__name__,
        as_valid_key(get_type_hints(some_func)),
    )
    assert expected == func.key()
    assert _generate_key(some_func) == func.key()


def test_overload() -> None:
    """Tests the overload decorator."""

    @dataclass
    class Some:
        text: str = "Hello"

    @overload
    def some_func(str_1: str, int_1: int):
        return str_1 + str(int_1)

    @overload  # type: ignore
    def some_func(str_1: str):  # noqa: F811
        return str_1

    @overload  # type: ignore
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
    with pytest.raises(NoFunctionFoundError) as excinfo:
        some_func(int_1=1)
    # print(excinfo)
    assert "No matching function found." in str(excinfo)
    assert some_func(int_1=1, str_1="Number: ") == "Number: 1"
    assert some_func(Some()) == "Hello"
    assert some_func(obj=Some()) == "Hello"


def test_overload_on_class_method() -> None:
    """Test overload of methods."""

    @dataclass
    class Hello:
        text: str = "Hello"

    class Some:
        def __init__(self) -> None:
            pass

        @overload
        def func(self, str_1: str, int_1: int) -> str:
            return str_1 + str(int_1)

        @overload  # type: ignore
        def func(self, str_1: str) -> str:  # noqa: F811
            return str_1

        @overload  # type: ignore
        def func(self, obj: Hello) -> str:  # noqa: F811
            return obj.text

    @overload
    def func(str_1: str) -> str:
        return "yummy " + str_1

    some = Some()
    some_func = some.func
    kwargs = {"str_1": "Number: ", "int_1": 1}
    args = ["Number: ", 1]
    assert some.func(**kwargs) == "Number: 1"
    assert some.func(*args) == "Number: 1"
    assert some_func(**kwargs) == "Number: 1"
    assert some_func(*args) == "Number: 1"
    assert some_func("cheese") == "cheese"
    assert func("cheese") == "yummy cheese"
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
    with pytest.raises(NoFunctionFoundError) as excinfo:
        some_func(int_1=1)
    assert "def func(int_1: int):" in str(excinfo)
    assert "Following definitions of" in str(excinfo)
    assert "No matching function found." in str(excinfo)
    assert some_func(int_1=1, str_1="Number: ") == "Number: 1"
    assert some_func(Hello()) == "Hello"
    assert some_func(obj=Hello()) == "Hello"


def test_namespacekey() -> None:
    """Test string representation and other features of NamespaceKey."""

    @overload
    def some_func(str_1: str, int_1: int):
        return str_1 + str(int_1)

    @overload  # type: ignore
    def some_func(str_1: str):  # noqa: F811
        return str_1

    assert some_func.key().unordered.unordered == some_func.key().unordered
    assert "def some_func(str_1: str, int_1: int):" in func_versions_info(some_func)
    assert str(some_func.key().unordered) == some_func.key().unordered._str_unordered()
