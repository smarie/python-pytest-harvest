# Changelog

### 0.7.0 - Documentation + `get_session_synthesis_dct` improvements 2

 * Results bags do not measure execution time anymore since this is much less accurate than pytest duration. Fixes [#6](https://github.com/smarie/python-pytest-harvest/issues/6)
 
 * `get_session_synthesis_dct` does not output the stage by stage details (setup/call/teardown) anymore by default, but a new option `status_details` allows users to enable them. Fixes [#5](https://github.com/smarie/python-pytest-harvest/issues/5)
   
 * `get_session_synthesis_dct` has also 2 new options `durations_in_ms` and `pytest_prefix` to better control the output.

 * Improved documentation.

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
