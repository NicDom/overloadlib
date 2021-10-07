"""test_overloadlib.py.

Tests the module overloadlib.py
"""

from typing import Any
from typing import Callable
from typing import Dict
from typing import Tuple
from typing import Union
from typing import get_type_hints

from dataclasses import dataclass

import pytest

from overloadlib.overloadlib import Function
from overloadlib.overloadlib import NamespaceKey
from overloadlib.overloadlib import NoFunctionFoundError
from overloadlib.overloadlib import _generate_key
from overloadlib.overloadlib import func_versions_info
from overloadlib.overloadlib import overload
from overloadlib.overloadlib import override


def check_exceptions(func: Union[Function, Callable[..., Any]]) -> None:
    """Checks all exceptions for the `Function` `func`.

    Args:
        func (Function): The Functions, whose exceptions raises are to
            be checked.
    """
    with pytest.raises(TypeError) as excinfo:
        func(str_1=2)
    assert "'str_1' needs to be of type" in str(excinfo)
    with pytest.raises(TypeError) as excinfo:
        func(str_1="Number: ", int_1="1")
    assert "'int_1' needs to be of type" in str(excinfo)
    with pytest.raises(TypeError) as excinfo:
        func(obj=2)
    assert "is type" in str(excinfo) and f"{int}" in str(excinfo)
    with pytest.raises(NoFunctionFoundError) as excinfo:
        func(int_1=1)
    assert "(int_1: int):" in str(excinfo)
    assert "Following definitions of" in str(excinfo)
    assert "No matching function found." in str(excinfo)
    with pytest.raises(NoFunctionFoundError) as excinfo:
        func(1)
    assert "(int)" in str(excinfo)


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
    keys = tuple(key for key in dictionary.keys())
    values = tuple(value for value in dictionary.values())
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

    @overload  # type: ignore
    def some_func():  # noqa: F811
        return "I am empty"

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
    assert "No matching function found." in str(excinfo)
    with pytest.raises(NoFunctionFoundError) as excinfo:
        some_func(1)
    assert "(int)" in str(excinfo)
    assert some_func(int_1=1, str_1="Number: ") == "Number: 1"
    assert some_func(Some()) == "Hello"
    assert some_func(obj=Some()) == "Hello"
    assert some_func() == "I am empty"


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

        @overload  # type: ignore
        def func(self):  # noqa: F811
            return "I am empty"

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
    check_exceptions(some_func)
    assert some_func(int_1=1, str_1="Number: ") == "Number: 1"
    assert some_func(Hello()) == "Hello"
    assert some_func(obj=Hello()) == "Hello"
    assert some_func() == "I am empty"


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


def test_override() -> None:
    """Overrides functions."""

    def func_str(var: str) -> str:
        return "I am a string"

    def func_int(var: int) -> str:
        return "I am an integer"

    @overload
    def func_both(var_1: int, var_2: str) -> str:
        return var_2 * var_1

    @override(funcs=[func_str, func_int, func_both])
    def new_func(fl: float) -> str:
        return "Float parameter"

    assert new_func(1.0) == "Float parameter"
    assert new_func("a") == func_str("a") == "I am a string"
    assert new_func(1) == func_int(1) == "I am an integer"
    assert new_func(1, "a") == func_both(1, "a") == "a"


def test_add() -> None:
    """Adds function call to an existing `Function`."""

    @dataclass
    class Some:
        text: str = "Hello"

    @overload
    def some_func(str_1: str, int_1: int) -> str:
        return str_1 + str(int_1)

    @some_func.add
    def _(str_1: str) -> str:
        return str_1

    @some_func.add
    def name_does_not_matter(obj: Some) -> str:
        return obj.text

    @some_func.add  # type: ignore[no-redef]
    def _(str_1: str, str_2: str) -> str:
        return str_1 + str_2

    assert some_func("This is a number: ", 10) == "This is a number: 10"
    assert some_func("cheese") == "cheese"
    assert some_func(Some()) == "Hello"
    check_exceptions(some_func)
