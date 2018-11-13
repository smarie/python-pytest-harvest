# Changelog

### 0.6.0 - `get_session_synthesis_dct` improvements

 * `get_session_synthesis_dct` now has a test object `filter`, a `flatten` option, and and can now take optional storage objects as input to create a fully merged dictionary. See `help(get_session_synthesis_dct)` for details. Fixes [#3](https://github.com/smarie/python-pytest-harvest/issues/3).

### 0.5.1 - Fixed bug with pytest 2.x

 * Fixed [#2](https://github.com/smarie/python-pytest-harvest/issues/2).

### 0.5.0 - First public version

First version validated against the [data science benchmark pattern](https://smarie.github.io/pytest-patterns/) (yet to be published)

 * `get_session_synthesis_dct` method to collect various test information already available
 * `@saved_fixture` decorator supports both a variable or a fixture for the storage
 * `create_results_bag_fixture` to create results bags
 * Documentation
