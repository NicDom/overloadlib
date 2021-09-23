from copy import deepcopy  # noqa: D100
from typing import Any
from typing import Callable
from typing import Dict
from typing import get_type_hints
from typing import List
from typing import NewType
from typing import Optional
from typing import Tuple
from typing import Type


__all__ = ["Function", "Namespace", "overload"]

NamespaceKey = NewType("NamespaceKey", Tuple[str, str, str, Any])


class Function(object):
    """Function is a wrap over standard python function."""

    def __init__(self, fn: Callable) -> None:
        """__init__ methode of `Function`.

        Args:
            fn (Callable): The function to be wrapped.
        """
        self.fn: Callable = fn

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Overriding the __call__ function which makes the instance callable.

        Args:
            args (Any): Arguments given to the function.
            kwargs (Any): Keyword-arguments given to the function.

        Raises:
            Exception: If no matching function was found.

        Returns:
            Any: The value of the function.
        """
        # fetching the function to be invoked from the virtual namespace
        # through the arguments.
        fn = Namespace.get_instance().get(self.fn, *args, **kwargs)
        if not fn:
            raise Exception("No matching function found.")

        # invoking the wrapped function and returning the value.
        return fn(*args, **kwargs)

    def as_valid_key(self, dictionary: Dict[Any, Any]) -> Tuple[tuple, tuple]:
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
        arg_dict = dict()
        if args is None:
            args = self.as_valid_key(get_type_hints(self.fn))
        else:
            if kwargs != {}:
                for key, value in kwargs.items():
                    arg_dict[key] = type(value)
                args = self.as_valid_key(arg_dict)
            else:
                args = tuple([type(args[i]) for i in range(len(args))])

        return tuple(
            [
                self.fn.__module__,
                self.fn.__class__,
                self.fn.__name__,
                args,
            ]
        )


class Namespace(object):
    """Singleton class that is responsible for holding all the functions."""

    __instance = None

    def __init__(self) -> None:
        """__init__-methode for class `Namespace`.

        Raises:
            Exception: If a instance of Namespace already exists.
        """
        if self.__instance is None:
            self.function_map = dict()
            Namespace.__instance = self
        else:
            raise Exception(
                "Cannot instantiate a virtual Namespace again"
            )  # pragma: no cover

    @staticmethod
    def get_instance() -> Type["Namespace"]:
        """Returns an instance of `Namespace`, if no other exists.

        Returns:
            Namespace: An instance of Namespace.
        """
        if Namespace.__instance is None:
            Namespace()
        return Namespace.__instance

    def register(self, fn: Callable) -> Type[Function]:
        """Registers the function in the virtual namespace.

        Registers the function in the virtual namespace and returns
        an instance of callable Function that wraps the
        function fn.

        Args:
            fn (Callable): The function to be registered.

        Returns:
            Type[Function]: The wrapped function `Function(fn)`.
        """
        func = Function(fn)
        self.function_map[func.key()] = fn
        return func

    def get(self, fn: Callable, *args: Any, **kwargs: Any) -> Optional[Function]:
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
            print(excinfo)
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
        """
        results = []
        for val_key in val_keys:
            keys = val_key[-1][0]
            values = val_key[-1][-1]
            result = [
                f"'{key}' needs to be of type {value}\n"
                for key, value in zip(keys, values)
            ]
            results += result
        return results

    def keys_matching_func_name(self, func_key: NamespaceKey) -> List[NamespaceKey]:
        """Returns the keys that match the functionname, -module and -class.

        Args:
            func_key (NamespaceKey): The NamespaceKey of the function.

        Returns:
            List[NamespaceKey]: The matching NamespaceKeys
        """
        return [key for key in self.function_map.keys() if key[0:-1] == func_key[0:-1]]

    def match_only_by_type(self, func_key: NamespaceKey) -> Optional[Function]:
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
            args = key[-1][-1]
            # print("key_args", args)
            if func_key[-1] == args:
                return self.function_map.get(key)
        return None

    def match_by_kwargs(self, func_key: NamespaceKey) -> Optional[Function]:
        """Returns the wrapped function using the keyword arguments of the function.

        Neglects the order of the keywords.

        Args:
            func_key (NamespaceKey): The NamespaceKey of the function.

        Returns:
            Optional[Function]: The wrapped function, if a match was found,
                None otherwise.
        """
        if isinstance(func_key[-1][0], tuple):
            frozenset_func_key = self.frozen_key(func_key)
            copy = tuple([self.frozen_key(key) for key in self.function_map.keys()])
            key_dict = dict(zip(copy, self.function_map.keys()))
            match = key_dict.get(frozenset_func_key)
            return self.function_map.get(match)
        return None

    def frozen_key(self, key: NamespaceKey) -> NamespaceKey:
        """Returns type and argumentnames of a key un-ordered.

        Args:
            key (NamespaceKey): Some NamespaceKey

        Returns:
            NamespaceKey: The unordered key.
        """
        key = deepcopy(key)
        return tuple(list(*key[0:1]) + [frozenset(dict(zip(key[-1][0], key[-1][1])))])

    def func_arg_names_matchin_kwargs_keys(
        self, func_key: NamespaceKey
    ) -> List[NamespaceKey]:
        """The namespace-keys whose argnames fit the function keyword-arguments.

        Args:
            func_key (NamespaceKey): The key of the function.

        Returns:
            List[NamespaceKey]: The matching keys in the virtual namespace.
        """
        opt_keys = self.keys_matching_func_name(func_key=func_key)
        func_key_kwarg_keys = (
            func_key[-1][0] if isinstance(func_key[-1][0], tuple) else None
        )
        return [key for key in opt_keys if func_key_kwarg_keys == key[-1][0]]


def overload(fn: Callable) -> Function:
    """Decorator for overloading a function.

    Overload is the decorator that wraps the function
    and returns a callable object of type Function.

    Args:
        fn (Callable): The callable to be overloaded.

    Returns:
        Function: The registered and wrapped function `fn`.
    """
    return Namespace.get_instance().register(fn)
