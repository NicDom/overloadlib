Overloadlib
===========

|PyPI| |Status| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/overloadlib.svg
   :target: https://pypi.org/project/overloadlib/
   :alt: PyPI
.. |Status| image:: https://img.shields.io/pypi/status/overloadlib.svg
   :target: https://pypi.org/project/overloadlib/
   :alt: Status
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/overloadlib
   :target: https://pypi.org/project/overloadlib
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/overloadlib
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/overloadlib/latest.svg?label=Read%20the%20Docs
   :target: https://overloadlib.readthedocs.io/
   :alt: Read the documentation at https://overloadlib.readthedocs.io/
.. |Tests| image:: https://github.com/NicDom/overloadlib/workflows/Tests/badge.svg
   :target: https://github.com/NicDom/overloadlib/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/NicDom/overloadlib/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/NicDom/overloadlib
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black


Features
--------

* Introduces ``@overload`` and ``@override`` decorators, allowing one to overload and override functions. Functions are then called according to their argument types:

.. code-block:: python

   @overload
   def func(var: str):
      return var

   @overload
   def func(var: int):
      return str(var * 5)

   func("a") == "a"  # True
   "a: " + func(1)  # "a: 5"

* Raises human readable errors, if no callable was determined with the given arguments. For example the following given:

.. code-block:: python

   @overload
   def some_func(str_1: str, int_1: int):
      return str_1 + str(int_1)

   @overload
   def some_func(str_1: str):
      return str_1

Calling:

.. code::

    >>> some_func(str_1=2)
    PyOverloadError:
    Error when calling:
    (__main__.some_func):
            def some_func(str_1: int):
                    ...:
            'str_1' needs to be of type (<class 'str'>,) (is type <class 'int'>)

or

.. code-block:: python

    >>> some_func(10)
    __main__.NoFunctionFoundError: No matching function found.
    Following definitions of 'some_func' were found:
    (__main__.some_func):
            def some_func(str_1: str, int_1: int):
                    ...
    (__main__.some_func):
            def some_func(str_1: str):
                    ...
    The following call was made:
    (__main__.some_func):
            def some_func(int_1: int):
                    ...

* Any type of variables is allowed: Build-in ones like ``str, int, List`` but also own ones, like classes etc.
* ``@overload`` uses ``get_type_hints`` to identify the right function call via type-checking. Hence, it may also be used as a type-checker for functions.
* Forgot, which overloads of a specific function have been implemented? No worries, you can print them with their typing information using `print(func_versions_info(<my_func>))`, e.g.

.. code-block::

   >>> print(func_versions_info(some_func))

   Following overloads of 'some_func' exist:
   (__main__.some_func):
            def some_func(str_1: str, int_1: int):
                  ...
   (__main__.some_func):
            def some_func(str_1: str):
                  ...



Requirements
------------

Requires Python 3.7+.


Installation
------------

You can install *Overloadlib* via pip_ from PyPI_:

.. code:: console

   $ pip install overloadlib

or install with  ``Poetry``

.. code:: console

   $ poetry add overloadlib


Then you can run

.. code:: console

   $ overloadlib --help


or with  ``Poetry``:

.. code:: console

   $ poetry run overloadlib --help


<details>
<summary>Installing Poetry</summary>
<p>

To download and install Poetry run (with curl):

.. code:: console

   $ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -


or on windows (without curl):

.. code:: console

   $ (Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py -UseBasicParsing).Content | python -


</p>
</details>

Uninstall
~~~~~~~~~

If you wan to uninstall the package, simply run

.. code:: console

   $ pip uninstall overloadlib


or with  ``Poetry``:

.. code:: console

   $ poetry remove overloadlib




Usage
-----

Please see the `Command-line Reference <Usage_>`_ for details.


Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the `MIT license`_,
*Overloadlib* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------

This project was generated by a template inspired by `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template and  `@TezRomacH`_'s `python-package-template`_

.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter.
.. _python-package-template: https://github.com/TezRomacH/python-package-template
.. _@TezRomacH: https://github.com/TezRomacH
.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/NicDom/overloadlib/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://overloadlib.readthedocs.io/en/latest/usage.html
