Usage
=====

.. raw:: html

   <details>
   <summary>Import
   </summary>
   <p>

Imports need to come form ``overloadlib.overloadlib``. Importing via

.. code:: python

   from overloadlib.overloadlib import *

imports ``overload`` and ``override`` decorators, as well as
``func_versions_info``.

.. raw:: html

   </p>
   </details>

|

Overloading of functions can be done via the ``@overload`` or
``@override`` decorator.

@overload
~~~~~~~~~

Overloading of functions:

.. code:: python

   @overload
   def func(var: str):
       return var

   @overload
   def func(var: int):
       return str(var * 5)

   func("a") == "a"  # True
   "a: " + func(1)  # "a: 5"

Overloading of methods (or mixtures of both) are also possible using the
same decorator:

.. code:: python

   @dataclass
   class Hello:
       text: str = "Hello"

   class Some:
       def __init__(self) -> None:
           pass

       @overload
       def func(self, str_1: str, int_1: int) -> str:
           return str_1 + str(int_1)

       @overload
       def func(self, str_1: str) -> str:
           return str_1

       @overload
       def func(self, obj: Hello) -> str:
           return obj.text

   @overload
   def func(str_1: str) -> str:
       return "yummy " + str_1

Note that own classes, can be given as types to the function.
Furthermore, methods and functions ma have the same name. Possible calls
could now look like this:

.. code:: python

   # Giving only *args
   some.func("Number: ", 1)  # "Number: 1"

   # Giving **kwargs
   some.func(str_1="Number: ", int_1=1)  # "Number: 1"

   # An object as argument
   some.func(Hello())  # "Hello"

   # Calling the function not the method
   func("yummy")  # "yummy cheese"

@override
~~~~~~~~~

You may also ‘overload’ functions using the ``@override`` decorator.
This one overrides an list of callables or ``Function`` (function
wrapper class of ``overloadlib.py``.) via a given new ‘parent’ function.

.. code:: python

   def func_str(var: str) -> str:
       return "I am a string"

   def func_int(var: int) -> str:
       return "I am an integer"

   @overload
   def func_both(var_1: int, var_2: str) -> str:
       return var_2 * var_1

   @override(funcs=[func_str, func_int, func_both])  # callables and `Function` are given
   def new_func(fl: float) -> str:
       return "Float parameter"

Possible calls could now look like this:

.. code:: python

   new_func(1.0) == "Float parameter"  # True
   new_func("a") == func_str("a") == "I am a string"  # True
   new_func(1) == func_int(1) == "I am an integer"  # True
   new_func(1, "a") == func_both(1, "a") == "a"  # True

Overriding ``Function``\ ’s (callables that are decorated with
``@overload``) overrides every *version* of that ``Function``:

.. code:: python

   @dataclass
   class Some:
       text: str = "Hello"

   @overload
   def func(str_1: str) -> str:
       return str_1

   @func.add
   def _(obj: Some) -> str:
       return obj.text

   @overload
   def func() -> str:
       return "Functions don't need to have arguments."

   # adds all previously defined overloads/'version' of `func` to `new`
   @override(funcs=[func])
   def new(str_1: str, int_1: int) -> str:
       return str_1 * int_1

   assert new("a") == "a" == func("a")
   assert new(Some()) == "Hello" == func(Some())
   assert new() == "Functions don't need to have arguments." == func()
   assert new("house", 2) == "househouse"

@<Function>.add
~~~~~~~~~~~~~~~

You can always add a new callable to an existing *overloaded* callable
``<func>`` using the ``@<func>.add`` decorator:

.. code:: python


   @overload
   def some_func(str_1: str, int_1: int) -> str:
       return str_1 + str(int_1)

   @some_func.add
   def _(str_1: str) -> str:
       return str_1

   @some_func.add
   def name_does_not_matter() -> str:
       return "I return some text."

   @some_func.add
   def _(str_1: str, str_2: str) -> str:
       return str_1 + str_2

   assert some_func("This is a number: ", 10) == "This is a number: 10"
   assert some_func("cheese") == "cheese"
   assert some_func(Some()) == "Hello"

The name of the callable’s you are adding don’t matter and you can also
always use the same name, when adding. However, as using the same name
for added functions, clashes with ``[no-redef]`` error of mypy_, it is
recommended to use different ones (this also increases the readability
of the code). [1]_

Usage of ``@override`` and ``@<Function>.add`` is recommended over usage
of ``@overload`` only, when working with static type checkers like mypy_.

.. [1]
   It should also be stressed, that ``@<func>.add`` only works with a
   previously with ``@overload`` decorated function \`.

func_versions_info
~~~~~~~~~~~~~~~~~~

If you want to get all versions of a certain function ``<myfunc>``, use
``func_versions_info(<myfunc>)``, e.g.

.. code:: python

   >>> print(func_versions_info(new_func))

   Following overloads of 'new_func' exist:
   (__main__.new_func):
            def new_func(var: str):
                   ...
   (__main__.new_func):
            def new_func(var: int):
                   ...
   (__main__.new_func):
            def new_func(var_1: int, var_2: str):
                   ...
   (__main__.new_func):
            def new_func(fl: float):
                   ...

Common Mistakes and Limitations
-------------------------------

-  Overloading using overload raises problems with mypy_. This can be circumvented using ``@override`` (or ``@<func>.add``) instead of ``@overload``.

.. _mypy : http://mypy-lang.org/
