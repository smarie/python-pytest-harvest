# Changelog

### 1.5.0 - Bug fixes concerning fixtures

The `fixture_store` fixture, provided by the plugin, does not have `autouse=True` anymore. Fixed [#20](https://github.com/smarie/python-pytest-harvest/issues/20).

`get_all_pytest_fixture_names` now returns fixtures that are indirectly parametrized, as well as fixtures that are not parametrized. Fixed [#19](https://github.com/smarie/python-pytest-harvest/issues/19).

### 1.4.3 - Better exceptions for `@saved_fixture`

Now raising a better exception if `@saved_fixture` is used on session- or module-scope fixtures. Fixes [#18](https://github.com/smarie/python-pytest-harvest/issues/18)

### 1.4.2 - Fixed results bags in presence of steps (2)

Another import error was causing results bag to be saved incorrectly in presence of steps.

### 1.4.1 - Fixed results bags in presence of steps

Results bags are now compliant with `pytest-steps`: there are now one per step. This fixed [#16](https://github.com/smarie/python-pytest-harvest/issues/16).

### 1.4.0 - Removed integration with `pytest_steps` in default fixtures

Integrating `pytest-steps` in default fixtures seemed like a bad idea because it led to automatic behaviour that could silently raise warnings. Let `pytest-steps` handle it on its side.

### 1.3.0 - Better integration with `pytest_steps` in default fixtures

Default fixtures `module_results_df` and `session_results_df` now automatically become multi-level indexed when pytest steps is installed and there are steps in the tests.

### 1.2.1 - Minor: new low-level API

New method `get_all_pytest_fixture_names` to list all fixture names used by items in a session.

### 1.2.0 - Added column in default dataframe synthesis fixtures

Fixtures `module_results_df` and `session_results_df` now contains the `'pytest_obj'` column.

### 1.1.0 - New default fixtures + fixture parameter names fix

Created 6 fixtures registered by default by the plugin. Fixed [#14](https://github.com/smarie/python-pytest-harvest/issues/14):

 - `fixture_store` in an `OrderedDict` that can be used as a fixture store, typically in `@saved_fixture`.
 - `results_bag` is a `ResultsBag`-typed results bag.
 - `session_results_dct` and `module_results_dct` return a synthesis dictionary for all tests completed "so far", respectively in the session or module. They include
    contents from the default `fixture_store`, including `results_bag`.
 - `session_results_df` and `module_results_df` are the dataframe equivalents of `session_results_dct` and `module_results_dct`

The documentation has been updated so that users can get started more quickly by leveraging them.

In addition:

 - `get_session_synthesis_dct` can now take both a `session` or a `request` input. If a `request` is provided, the status of current item will be marked as 'pending', while not started items will be marked as 'unknown'.
 - fixed bug in `get_session_synthesis_dct`: fixture parameters and saved fixtures where overriding each other in the final dict in `flatten=True` mode. Now fixture parameters appear as `'<fixture_name>_param'`. Fixed [#15](https://github.com/smarie/python-pytest-harvest/issues/15).
 - `@saved_fixture` can now be used without arguments. By default it will store fixtures in the default session-scoped `'fixture_store'` fixture.
 - `HARVEST_PREFIX` moved to `common.py` and is now exported at package level.


### 1.0.1 - Ordering bug fix

Fixed pytest ordering issue, by relying on [place_as](https://github.com/pytest-dev/pytest/issues/4429). See [#18](https://github.com/smarie/python-pytest-steps/issues/18)

### 1.0.0 - new methods for pytest session analysis

New methods are provided to analyse pytest session results: 
 - `filter_session_items(session, filter=None)` is the filtering method used behind several functions in this package - it can be used independently. `pytest_item_matches_filter` is the inner method used to test if a single item matches the filter.
 - `get_all_pytest_param_names(session, filter=None, filter_incomplete=False)` lists all unique parameter names used in pytest session items, with optional filtering capabilities. Fixes [#12](https://github.com/smarie/python-pytest-harvest/issues/12)
 - `is_pytest_incomplete(item)`, `get_pytest_status(item)`, `get_pytest_param_names(item)` and `get_pytest_params(item)` allow users to analyse a specific item. 


### 0.9.0 - `get_session_synthesis_dct`: filter bugfix + test id formatter

 * `get_session_synthesis_dct`:
  
   - `filter` now correctly handles class methods. Fixed [#11](https://github.com/smarie/python-pytest-harvest/issues/11)
   - new `test_id_format` option to process test ids. Fixed [#9](https://github.com/smarie/python-pytest-harvest/issues/9)

### 0.8.0 - Documentation + better filters in `get_session_synthesis_dct`

 * Documentation: added a section about creating the synthesis table from *inside* a test function (fixes [#4](https://github.com/smarie/python-pytest-harvest/issues/4)). Also, added a link to a complete example file.
 
 * `get_session_synthesis_dct`: `filter` argument can now contain module names (fixed [#7](https://github.com/smarie/python-pytest-harvest/issues/7)). Also now the function filters out incomplete tests by default. A new `filter_incomplete` argument can be used to display them again (fixed [#8](https://github.com/smarie/python-pytest-harvest/issues/8)).

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
