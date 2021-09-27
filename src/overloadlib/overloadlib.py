"""overloadlib.py.

Implements `overload` feature in python.
"""

from typing import Any
from typing import Callable
from typing import Dict
from typing import FrozenSet
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from typing import get_type_hints

from dataclasses import dataclass
from functools import partial
from functools import wraps

__all__ = ["Function", "Namespace", "overload"]


ArgsType = Optional[List[Any]]
KwargsType = Optional[Dict[str, Any]]
NspKeyTypeHints = Union[
    Tuple[Tuple[Any, ...], Tuple[Any, ...]], Tuple[Any, ...], FrozenSet[Any]
]


@dataclass(frozen=True)
class NamespaceKey:
    """Frozen dataclass representing a namespace key.

    `Namespace` keys are the keys that uniquely identify an overloaded function
    or method. A `NamespaceKey` is generated whenever a function is overloaded and is
    used as a key in the (singleton) virtual namespace `Namespace` together with the
    overloaded function. If an overloaded function is called, another `NamespaceKey`
    corresponding to the given args and kwargs is generated and compared to the
    keys stored in the virtual namespace to determine the right version of the
    function.

    Attributes:
        module (str): The module of the overloaded function.
        qualname (str): The __qualname__ of the overloaded function.
        name (str): The __name__ of the overloaded function.
        type_hints (NspKeyTypeHints): The type_hints of the overloaded function. By
            default they stored as a tuple of two tuple: the first giving the arg-names,
            the second giving the the types of the args.
    """

    module: str
    qualname: str
    name: str
    type_hints: NspKeyTypeHints

    @property
    def unordered(self) -> "NamespaceKey":
        """Returns the NamespaceKey with "unordered" type hints.

        When comparing keys of the namespace to the one generated, when a function
        is called, the function was called with the right kwargs, but compared to
        the stored key in a different order. For these cases we have to create a
        frozen set of the tuple represting the type hints.

        Returns:
            NamespaceKey: The NamespaceKey `self`, but with the type hints stored as
                a frozen set.
        """
        if isinstance(self.type_hints, frozenset):
            return self
        if not isinstance(self.type_hints[0], tuple):  # pragma: no cover
            type_hints = frozenset(self.type_hints)
        else:
            type_hints = frozenset(
                dict(zip(self.type_hints[0], self.type_hints[1])).items()
            )
        return NamespaceKey(
            module=self.module,
            qualname=self.qualname,
            name=self.name,
            type_hints=type_hints,
        )

    @property
    def meta(self) -> Tuple[str, str, str]:
        """Returns the meta of the NamespaceKey.

        With meta of a NamespaceKey, we are referring to all information
        except the type hints, i.e. the module, the __qualname__ and the
        __name__ of the function, to which this key belongs. The meta are
        required, whenever we want to now, which `versions` of a certain
        function are stored in the singleton Namespace.

        Returns:
            Tuple[str, str, str]: The meta of the key: (module, qualname, name)
        """
        return (self.module, self.qualname, self.name)

    #######################################################
    #     FUNCTIONS FOR __STR__ REPRESENTATION (NamespaceKey)
    #######################################################

    def _str_for_type_hint_dict(self, type_hints: Dict[str, type]) -> str:
        """Private helper function for creating __str__.

        Called if `self.type_hints` are valid dict, and thus, only if the
        key is one stored in the namespace or a function was called using
        kwargs.

        Args:
            type_hints (Dict[str, type]): Type hints for the key.

        Returns:
            str: The string representation for the type_hints of the key.
        """
        return (
            f"\n\t def {self.name}("
            + ", ".join(
                [f"{key}: {value.__name__}" for key, value in type_hints.items()]
            )
            + "):\n\t\t..."
        )

    def _str_for_type_hint_tuple(self, type_hints: Tuple[Any, ...]) -> str:
        """Private helper function for creating __str__.

        Called if `self.type_hints` are valid list, and thus, only if the
        key was generated on a function call (using only args). Mostly
        used when debugging.

        Args:
            type_hints (Dict[str, type]): Type hints for the key.

        Returns:
            str: The string representation for the type_hints of the key.
        """
        return f"\n\t Received call as {self.name}(" + ", ".join(
            [f"{hint.__name__}" for hint in type_hints]
        )  # pragma: no cover

    def _str_unordered(self) -> str:  # pragma: no cover   # type: ignore
        """Private helper function for creating __str__.

        Called if the NamespaceKey type hints are unordered.

        Returns:
            str: String representation for an 'unordered' key.
        """
        msg = f"({self.module}.{self.qualname}):"
        try:
            type_hints = dict(self.type_hints)  # type: ignore
            msg += self._str_for_type_hint_dict(type_hints)
        except (TypeError, ValueError):
            type_hints = tuple(self.type_hints)  # type: ignore
            msg += self._str_for_type_hint_tuple(type_hints)  # type: ignore
        return msg

    def _str_ordered(self) -> str:  # pragma: no cover
        """Private helper function for creating __str__.

        Called if the NamespaceKey type hints are ordered.

        Returns:
            str: String representation for an 'ordered' key.
        """
        msg = f"({self.module}.{self.qualname}):"
        try:
            type_hints = dict(zip(self.type_hints[0], self.type_hints[1]))  # type: ignore # noqa: B950
            msg += self._str_for_type_hint_dict(type_hints)
        except (TypeError, ValueError):
            type_hints = self.type_hints  # type: ignore
            msg += self._str_for_type_hint_tuple(type_hints)  # type: ignore
        return msg

    def __str__(self) -> str:
        """String representation of the key.

        The string representation has the following form:
        (`self.module`.`self.qualname`):
            def self.name(arg_1: type(arg_1),...):
                ...

        Returns:
            str: The string representation of a key, e.g.
                "(module.Some.func):
                     def func(var: int, var_2: str):
                         ..."

        """
        if isinstance(self.type_hints, frozenset):
            return self._str_unordered()
        else:
            return self._str_ordered()

    ############################################################
    #  END OF FUNCTIONS FOR __STR__ REPRESENTATION (NamespaceKey)
    ############################################################


######################################
# SOME GENERALLY USED HELPER FUNCTIONS
######################################


def _overload_func_wrap(f: Callable[..., Any]) -> Callable[..., Any]:
    """Inserts `self`, if function is a method.

    Required as a function is only turned into a method, after
    the metaclass to the class was create.
    Used in `Function.__call__` for example.

    Args:
        f (Callable): The function we to wrap.

    Returns:
        Callable: The wrapped function, as a method if necessary

    Example:
        >>> class Some():
        >>>     @overload
        >>>     def func(self, var: str) -> str:
        >>>         return var
        >>> @overload
        >>> def func(var: str) -> str:
        >>>     return var * 5
        >>> assert func("a") == "aaaaa"
        >>> assert Some().func("a") == "a"
    """

    @wraps(f)
    def inner_func(_cls_or_self_: Any, *args: ArgsType, **kwargs: KwargsType) -> Any:
        if _cls_or_self_ is None:
            return f(*args, **kwargs)
        else:
            return f(_cls_or_self_, *args, **kwargs)

    return inner_func


def _as_ordered_key(
    dictionary: Dict[str, Any]
) -> Tuple[Tuple[Any, ...], Tuple[Any, ...]]:
    """Turns a dictionary into a tuple. Used at _generate_key.

    First entry is a tuple containing the key, second entry is tuple containing the
    values. Required to create a hashable object of the type-hints of a function,
    that can used for a dictionary key.

    Args:
        dictionary (Dict[Any, Any]): Some dictionary.

    Returns:
        Tuple[tuple, tuple]: The tuple.

    Example:
        >>> hints = {"a": 1, "b": 2}
        >>> assert _as_ordered_key(hints) == (('a', 'b'), (1, 2))
    """
    keys = tuple([key for key in dictionary.keys()])
    values = tuple([value for value in dictionary.values()])
    return (keys, values)


def _generate_key(
    func: Callable[..., Any], args: ArgsType = None, kwargs: KwargsType = None
) -> NamespaceKey:
    """Returns the key that will uniquely identify a function.

    Args:
        func (Callable): The function we want to generate a key for.
        args (ArgsType): The args given to the function. Defaults to None.
        kwargs (KwargsType): The keyword-arguments given to the function.
            Defaults to None.

    Returns:
        NamespaceKey: The NamespaceKey for the function,
    """
    arg_dict = dict()
    if kwargs is None:
        kwargs = dict()
    if args is None:
        hints = {
            key: value for key, value in get_type_hints(func).items() if key != "return"
        }
        type_hints = _as_ordered_key(hints)
    else:
        if kwargs != {}:
            for key, value in kwargs.items():
                arg_dict[key] = type(value)
            type_hints = _as_ordered_key(arg_dict)
        else:
            type_hints = tuple([type(args[i]) for i in range(len(args))])  # type: ignore # noqa: B950
    result = NamespaceKey(
        module=func.__module__,
        qualname=func.__qualname__,
        name=func.__name__,
        type_hints=type_hints,
    )
    return result


######################################
#            EXCEPTIONS
######################################


class PyOverloadError(TypeError):
    """The base class for exceptions."""


class NoFunctionFoundError(PyOverloadError):
    """The error, if no matching overloaded function was found."""

    def __init__(
        self,
        func_key: Optional[NamespaceKey] = None,
        message: str = "No matching function found.\n",
    ):
        self.func_key = func_key
        self.message = message
        if func_key is not None:  # pragma: no cover
            options = Namespace.get_instance().keys_matching_func_name(func_key)
            self.message += f"Following definitions of '{func_key.name}' were found:\n"
            self.message += "\n".join([key.__str__() for key in options])
            self.message += f"\nThe following function was given:\n{func_key}"
        super().__init__(self.message)

    # def __str__(self) -> str:
    #     return self.message


######################################
#          FUNCTION WRAPPER
######################################


class Function(partial):  # type: ignore
    """Class wrapping a callable.

    Subclass of functools.partial.

    Args:
        func (Callable): The function we want to wrap. (c.f. functools.partial)
        args (ArgsTape): Optional arguments. (c.f. functools.partial)
        keywors (KwargsType): Optional keywords. (c.f. functools.partial)
    """

    def __init__(
        self, func: Callable[..., Any], *args: ArgsType, **keywords: KwargsType
    ) -> None:
        """__init__ methode of `Function`.

        Sets the __qualname__ to wrapped functions __qualname__ initiates
        the owner of the function as None (required if function is a method)
        and calls super().__init__().

        Args:
            func (Callable[..., Any]): The function to be wrapped.
            *args (ArgsType): Additional optional args.
            **keywords (KwargsType): Additional optional kwargs.
        """
        super().__init__()  # type: ignore
        self.owner = None  # type: Optional[Union[Any, "Function"]]
        self.__qualname__ = self.func.__qualname__

    def __get__(self, owner: Any, owner_type: Optional[type] = None) -> "Function":
        """__get__-dunder method of Function.

        Required, when wrapped function is a method. Used to determine
        the correct owner of the methoed.

        Args:
            owner (Any): The object owning the method.
            owner_type ([type], optional): [description]. Defaults to None.

        Returns:
            Function: self
        """
        self.owner = owner or self
        return self

    def __call__(self, *args: ArgsType, **kwargs: KwargsType) -> Any:
        """Overriding the __call__ function which makes the instance callable.

        Args:
            args (ArgsType): Arguments given to the function.
            kwargs (KwargsType): Keyword-arguments given to the function.

        Raises:
            NoFunctionFoundError: If no matching function was found.

        Returns:
            Any: The value of the function.
        """
        # fetching the function to be invoked from the virtual namespace
        # through the arguments.
        fn = Namespace.get_instance().get(self.func, *args, **kwargs)
        if fn is None:
            raise NoFunctionFoundError(self.key(args, kwargs))

        # invoking the wrapped function and returning the value.
        func = _overload_func_wrap(fn)
        return func(self.owner, *args, **kwargs)

    def key(
        self, args: Optional[Any] = None, kwargs: Optional[Any] = None
    ) -> NamespaceKey:
        """Returns the key that will uniquely identify a function.

        Args:
            args (Any, optional): The args given to the function. Defaults to None.
            kwargs (Any, optional): The keyword-arguments given to the function.
                Defaults to None.

        Returns:
            NamespaceKey: The NamespaceKey for the function,
        """
        return _generate_key(self.func, args, kwargs)

    @property
    def __wrapped__(self) -> Callable[..., Any]:
        """__wrapped__- dunder property of `Function`.

        For example, required for `inspect.signature`

        Returns:
            Callable[..., Any]: The wrapped function.
        """
        return self.func


######################################
#       SINGLETON NAMESPACE
######################################


class Namespace(object):
    """Singleton class that is responsible for holding all the functions."""

    __instance: Optional["Namespace"] = None

    def __init__(self) -> None:
        """__init__-methode for class `Namespace`.

        Raises:
            Exception: If a instance of Namespace already exists.
        """
        if self.__instance is None:
            self.function_map: Dict[NamespaceKey, Callable[..., Any]] = dict()
            Namespace.__instance = self
        else:
            raise Exception(
                "Cannot instantiate a virtual Namespace again"
            )  # pragma: no cover

    @staticmethod
    def get_instance() -> "Namespace":
        """Returns an instance of `Namespace`, if no other exists.

        Returns:
            Namespace: An instance of Namespace.
        """
        if Namespace.__instance is None:
            Namespace()
        return Namespace.__instance  # type: ignore

    def register(self, fn: Callable[..., Any]) -> Function:
        """Registers the function in the virtual namespace.

        Registers the function in the virtual namespace and returns
        an instance of callable Function that wraps the
        function fn.

        Args:
            fn (Callable): The function to be registered.

        Returns:
            Function: The wrapped function `Function(fn)`.
        """
        func = Function(fn)
        self.function_map[func.key()] = fn
        return func

    def get(
        self, fn: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Optional[Callable[..., Any]]:
        """Returns the matching function.

        Tries to find the desired function for given args and kwargs using several
        approaches. At first, it compares only the types of the given arguments with the
        type patterns for the several overloaded version of the function `fn`. If no
        key, is matching the type pattern of the arguments, it raises an TypeError and
        prints the wrong types. If no exception occurred, it assumes that the arguments
        were given as keyword-arguments and checks again without caring for the
        postition of the arguments.

        Args:
            fn (Callable): The overloaded function.
            args (Any, optional): The args given to the function `fn`.
            kwargs (Any, optional): The keyword-arguments given to the function `fn`.

        Returns:
            Optional[Function]: The overloaded wrapped function `Function(fn)`,
                if a version fitting the given argument names and/or types exists,
                None otherwise.

        Raises:
            TypeError: If the arguments have the correct keywords,
                but wrong variable types.
        """
        func = Function(fn)
        func_key = func.key(args=args, kwargs=kwargs)

        # Check if given argument types fit one of the namespace key argument types
        valid_key = self.match_only_by_type(func_key=func_key)
        similar_keys = self.func_arg_names_matchin_kwargs_keys(func_key)
        result = self.function_map.get(func_key) or valid_key

        # func_key is not in namespace and argument types fo not fit to any namespace
        # key -> raise(ValueError)
        if result is None and similar_keys != []:
            excinfo = "".join(self.difference(similar_keys))
            raise (TypeError(excinfo))

        return self.match_by_kwargs(func_key=func_key) or self.match_only_by_type(
            func_key=func_key
        )

    def difference(self, val_keys: List[NamespaceKey]) -> List[str]:
        """Returns the typing information to `similar_keys` (c.f. `get`).

        Args:
            val_keys (List[NamespaceKey]): The `similar_keys`.

        Returns:
            List[str]: List containing the typing information.

        Raises:
            TypeError: if one of the NamespaceKeys in `val_keys` is
                unordered.
        """
        results = []
        for val_key in val_keys:
            if not isinstance(val_key.type_hints, frozenset):
                keys = val_key.type_hints[0]
                values = val_key.type_hints[-1]
                result = [
                    f"'{key}' needs to be of type {value}\n"
                    for key, value in zip(keys, values)
                ]
                results += result
            else:
                raise (
                    TypeError(
                        f"{val_key!r} is an unordered key, but keys need to ordered."
                    )
                )  # pragma: no cover

        return results

    def keys_matching_func_name(self, func_key: NamespaceKey) -> List[NamespaceKey]:
        """Returns the keys that match the functionname, -module and -class.

        Args:
            func_key (NamespaceKey): The NamespaceKey of the function.

        Returns:
            List[NamespaceKey]: The matching NamespaceKeys
        """
        return [key for key in self.function_map.keys() if key.meta == func_key.meta]

    def match_only_by_type(
        self, func_key: NamespaceKey
    ) -> Optional[Callable[..., Any]]:
        """Returns the wrapped function, if a type-match was found.

        Compares only the namespace keys, given by `keys_matching_func_name`. A
        type-match is found, if the types of the given function arguments match to the
        types of one of the Namespace keys.

        Args:
            func_key (NamespaceKey): The NamespaceKey of the function.

        Returns:
            Optional[Function]: The wrapped function,
                if a type-match was found, None otherwise.
        """
        opt_keys = self.keys_matching_func_name(func_key=func_key)
        for key in opt_keys:
            args = key.type_hints[-1]  # type: ignore
            if func_key.type_hints == args:
                return self.function_map.get(key)
        return None

    def match_by_kwargs(self, func_key: NamespaceKey) -> Optional[Callable[..., Any]]:
        """Returns the wrapped function using the keyword arguments of the function.

        Neglects the order of the keywords.

        Args:
            func_key (NamespaceKey): The NamespaceKey of the function.

        Returns:
            Optional[Function]: The wrapped function, if a match was found,
                None otherwise.
        """
        if not isinstance(func_key.type_hints, frozenset):
            copy = tuple([key.unordered for key in self.function_map.keys()])
            key_dict = dict(zip(copy, self.function_map.keys()))
            match = key_dict.get(func_key.unordered)
            return self.function_map.get(match)  # type: ignore
        return None  # pragma: no cover

    def func_arg_names_matchin_kwargs_keys(
        self, func_key: NamespaceKey
    ) -> List[NamespaceKey]:
        """The namespace-keys whose argnames fit the function keyword-arguments.

        Args:
            func_key (NamespaceKey): The key of the function.

        Returns:
            List[NamespaceKey]: The matching keys in the virtual namespace.
        """
        if not isinstance(func_key.type_hints, frozenset):
            opt_keys = self.keys_matching_func_name(func_key=func_key)
            return [
                key
                for key in opt_keys
                if func_key.type_hints[0]
                == key.type_hints[0]  # type:  ignore # noqa:  B950
            ]
        else:
            return []  # pragma: no cover


def overload(fn: Callable[..., Any]) -> Function:
    """Decorator for overloading a function.

    Overload is the decorator that wraps the function
    and returns a callable object of type Function.

    Args:
        fn (Callable): The callable to be overloaded.

    Returns:
        Function: The registered and wrapped function `fn`.

    Example:
        >>> @overload
        >>> def func(var: str):
                return var

        >>> @overload
        >>> def func(var: int):
                return str(var * 5)
        >>> assert func("a") == "a"
        >>> "a: " + func(1)
        "a: 5"
    """
    return Namespace.get_instance().register(fn)


############################################################################
#  FUNCTIONS FOR RETURNING INFORMATION ON OVERLOADED FUNCTIONS/METHODS
############################################################################


def get_overloads(func: Function) -> List[NamespaceKey]:
    """Returns overloaded versions of a function.

    Args:
        func (Function): The function, whose versions we would
            like to know.

    Returns:
        List[NamespaceKey]: A list containing the existing NamespaceKey for
            the function `func`.

    Example:
        >>> @overload
        >>> def func(var: str):
                return var

        >>> @overload
        >>> def func(var: int):
                return str(var * 5)
        >>> @overload
        >>> def other_func():
                pass
        >>> assert _generate_key(other_func.__wrapped__) not in get_overload(func)
    """
    func_key = _generate_key(func.__wrapped__)
    return Namespace.get_instance().keys_matching_func_name(func_key)


def func_versions_info(func: Function) -> str:
    """Returns the information on versions of a function.

    Args:
        func (Function): The function, whose version we would like to
            print.

    Returns:
        str: String containing information on the several version of an
            overloaded function.

    Example:
        >>> @overload
        >>> def func(var: str):
                return var

        >>> @overload
        >>> def func(var: int):
                return str(var * 5)
        >>> @overload
        >>> def other_func():
                pass
        >>> print(func_versions_info(func))
        (__main__.func):
            def func(var: str):
                ...
        (__main__.func):
            def func(var: int):
                ...
    """
    msg = f"Following overloads of '{func.__qualname__}' exist:\n"
    msg += "\n".join([key.__str__() for key in get_overloads(func)])
    return msg
