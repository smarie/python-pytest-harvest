# API reference

## 1. Available fixtures

The following fixtures can be used in your tests as soon as the library is installed (no explicit plugin activation is required).

### *`results_bag`*

A *"results bag"* fixture: a dictionary where you can store anything (results, context, etc.) during your tests execution. It offers a "much"-like api: you can access all entries using the object protocol such as in `results_bag.a = 1`.

This fixture has function-scope so a new, empty instance is injected in each test node. 

There are several ways to gather all results after they have been stored. 

 * To get the raw stored results, use the `fixture_store` fixture: `fixture_store['results_bag']` will contain all result bags for all tests.
   
 * If you are interested in both the stored results AND some stored fixture values (through `@saved_fixture`), you might rather wish to leverage the following helpers:

     - use one of the `session_results_dct`, `module_results_dct`, `session_results_df` or `module_results_df` fixtures. They contain all available information, in a nicely summarized way.
       
     - use the `get_session_synthesis_dct(session)` helper method to create a similar synthesis than the above with more customization capabilities.

If you wish to create custom results bags similar to this one (for example to create several with different names), use [`create_results_bag_fixture`](#create_results_bag_fixture).

See [basic](./index.md#b-collecting-test-artifacts) and [advanced](./advanced_usage.md#3-creating-results-bags-fixtures-to-collect-test-artifacts) documentation for details.

### *`fixture_store`*

A 'fixture store' fixture: a dictionary where fixture instances can be saved.
    
By default
 
 * all fixtures decorated with [`@saved_fixture`](#saved_fixture) are saved in this store.
 * the [`results_bag`](#results_bag) fixture is also saved in this store.

To retrieve the contents of the store, you can:

 * create a test using this fixture and make sure that it is executed after all others. 
 * access this fixture from a dependent fixture and read its value in the setup or teardown script.
 * access this fixture from the `request` fixture using the [`get_fixture_value`](#get_fixture_value) helper method.

This fixture has session scope so it is unique across the whole session. 

### *`session_results_dct`*

This fixture contains a synthesis dictionary for all tests completed "so far", with 'full' id format. It includes contents from the default `fixture_store`, including `results_bag`.

Behind the scenes it relies on `get_session_synthesis_dct`.

This fixture has a function scope because we want its contents to be refreshed every time it is needed.

See [documentation](./index.md#c--collecting-a-synthesis) for details.

### *`module_results_dct`*

Same than [`session_results_dct`](#session_results_dct) but with module scope.

### *`session_results_df`*

This fixture contains a synthesis dataframe for all tests completed "so far" in the module of the caller,
with 'function' id format. It includes contents from the default `fixture_store`, including `results_bag`.

It is basically just a transformation of the `session_results_dct` fixture into a pandas `DataFrame`.

If `pytest-steps` is installed, the step ids will be extracted and the dataframe index will be multi-level
(test id without step, step id).

This fixture has a function scope because we want its contents to be refreshed every time it is needed.

See [documentation](./index.md#c--collecting-a-synthesis) for details.

### *`module_results_df`*

Same than [`session_results_df`](#session_results_df) but with module scope.


### Associated getter functions

For each of the above `[module/session]_results_[dct/df]` fixtures, an equivalent `get_<fixture_name>(session, ...)` is available. This allows users to access the same level of functionality than the fixture, in places where fixtures are not available (typically in a pytest hook such as the `pytest_sessionfinish` session finish hook)


## 2. Additional symbols

### a- Basic

#### `@saved_fixture`

```python
@saved_fixture(store='fixture_store',  # type: Union[str, Dict[str, Any]]
               key=None,               # type: str
               views=None,             # type: Dict[str, Callable[[Any], Any]]
               save_raw=None,          # type: bool
               )
```

Decorates a fixture so that it is saved in `store`. `store` can be a dict-like variable or a string representing a fixture name to a dict-like session-scoped fixture. By default it uses the global 'fixture_store' fixture provided by this plugin.

After executing all tests, `<store>` will contain a new item under key `<key>` (default is the name of the fixture). This item is a dictionary <test_id>: <fixture_value> for each test node where the fixture was setup.

```python
import pytest
from pytest_harvest import saved_fixture

@pytest.fixture
@saved_fixture
def dummy():
    return 1

def test_dummy(dummy):
    pass

def test_synthesis(fixture_store):
    print(fixture_store['dummy'])
```

Note that for session-scoped and module-scoped fixtures, not all test ids will appear in the store - only those for which the fixture was (re)created.

Users can save additional views created from the fixture instance by applying transforms (callable functions). To do this, users can provide a dictionary under the `views` argument, containing a `{<key>: <procedure>}` dict-like. For each entry, `<procedure>` will be applied on the fixture instance, and the result will be stored under `<key>`. `save_raw` controls whether the fixture instance should still be saved in this case (default: `True` if `views is None`, `False` otherwise).

**Parameters**

 - **store**: a dict-like object or a fixture name corresponding to a dict-like object. in this dictionary, a new entry will be added for the fixture. This entry will contain a dictionary <test_id>: <fixture_value> for each test node. By default fixtures are stored in the `fixture_store``fixture.
 - **key**: the name associated with the stored fixture in the store. By default this is the fixture name.
 - **views**: an optional dictionary that can be provided to store views created from the fixture, rather than (or in addition to, if `save_raw=True`) the fixture itself. The dict should contain a `{<key>: <procedure>}` dict-like. For each entry, `<procedure>` will be applied on the fixture instance, and the result will be stored under `<key>`.
 - **save_raw**: controls whether the fixture instance should be saved. `None` (Default) is an automatic behaviour meaning "`True` if `views is None`, `False` otherwise".
 
**Returns**: a fixture that will be stored

See [basic](./index.md#a--storing-fixture-instances) and [advanced](./advanced_usage.md#2-storingretrieving-fixtures) documentation for details.

#### `ResultsBag` class

The default type for result bags, used in the `results_bag` fixture and `create_results_bag_fixture` method.

It is a simple 'Munch', that is, a dual object/dict. It is hashable with a not very interesting hash, but at least a unique one in a python session (id(self)).

### b- Intermediate

#### `create_results_bag_fixture(...)`

```python
create_results_bag_fixture(store,               # type: Union[str, Dict[str, Any]]
                           name='results_bag',  # type: str
                           bag_type=None,       # type: Type[Any]
                           )
```

Creates a "results bag" fixture with name `name` stored in the given store (under key=`name`). By default results bags are instances of [`ResultsBag`](#resultsbag_class) but you can provide another `bag_type` if needed.

**Parameters**

 * store: a dict-like object or a fixture name corresponding to a dict-like object. in this dictionary, a new entry will be added for the fixture. This entry will contain a dictionary <test_id>: <fixture_value> for each test node.

 * name: the name associated with the stored fixture in the global store. By default this is 'results_bag'.

 * bag_type: the type of object to create as a results bag. Default: `ResultsBag`

### c- Advanced

#### `get_fixture_store(session)`

The default fixture store, that is also available through the `fixture_store` fixture, is `FIXTURE_STORE`. Accessing it directly might be needed in some cases where fixtures are not available (typically in some pytest hooks). However to be pytest xdist compliant, users should rather use `get_fixture_store(session)` in these cases.

#### `get_session_synthesis_dct(...)`

```python
get_session_synthesis_dct(session_or_request,
                          test_id_format='full',   #
                          status_details=False,    # type: bool
                          durations_in_ms=False,   # type: bool
                          pytest_prefix=None,      # type: bool
                          filter=None,             # type: Any
                          filter_incomplete=True,  # type: bool
                          flatten=False,           # type: bool
                          fixture_store=None,      # type: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]
                          flatten_more=None        # type: Union[str, Iterable[str], Mapping[str, str]]
                          )
```

Returns a dictionary containing a synthesis of what is available currently in the provided `pytest` `session` object.

For each entry, the key is the test id, and the value is a dictionary containing:

 - `'pytest_obj'`: the object under test, typically a test function
 - `'pytest_status'`: the overall status (`'failing'`, `'skipped'`, `'passed'`)
 - `'pytest_duration'`: the duration of the `'call'` step. By default this is the pytest unit (s) but if you set `durations_in_ms=True` it becomes (ms)
 - `'pytest_status_details'`: a dictionary containing step-by-step status details for all pytest steps (`'setup'`, `'call'`, `'teardown'`). This is only included if `status_details=True` (not by default)

It is possible to process the test id (the keys) using the `test_id_format` option. Let's assume that the id is 

`pytest_steps/tests_raw/test_wrapped_in_class.py::TestX::()::test_easy[p1-p2]`. 

Here are the returned test ids depending on the selected `test_id_format`

 - `'function'` will return `test_easy[p1-p2]`
 - `'class'` will return `TestX::()::test_easy[p1-p2]`
 - `'module'` will return `test_wrapped_in_class.py::TestX::()::test_easy[...]`
 - `'full'` will return the original id (this is the default behaviour)

In addition one can provide a custom string handling function that will be called for each test id to process.

The 'pytest' prefix in front of all these items (except `pytest_obj`) is by default added in non-flatten mode and removed in flatten mode. To force one of these you can set `pytest_prefix` to `True` or `False`.

An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test functions) and/or module names.

If this method is called before the end of the pytest session, some nodes might be incomplete, i.e. they will not have data for the three stages (setup/call/teardown). By default these nodes are filtered out but you can set `filter_incomplete=False` to make them appear. They will have a special 'pending' synthesis status.

An optional collection of storage objects can be provided, so as to merge them into the resulting dictionary.

Finally a `flatten_output` option allows users to get a flat dictionary output instead of nested status details, parameters dict, and storage dicts.

**Parameters**:

 - **session**: a pytest session object.
 - **test_id_format**: one of 'function', 'class', 'module', or 'full' (default), or a custom test id processing function.
 - **status_details**: a flag indicating if pytest status details per stage (setup/call/teardown) should be included. Default=`False`: only the pytest status summary is provided.
 - **durations_in_ms**: by default `pytest` measures durations in seconds so they are outputed in this unit. You can turn the flag to True to output milliseconds instead.
 - **pytest_prefix**: to add (True) or remove (False) the 'pytest_' prefix in front of status, duration and status details. Typically useful in flatten mode when the names are not ambiguous. By default it is None, which means =(not flatten)
 - **filter**: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use module names. See [`pytest_item_matches_filter`]().
 - **filter_incomplete**: a boolean indicating if incomplete nodes (without the three stages setup/call/teardown)
    should appear in the results (False) or not (True, default).
 - **flatten**: a boolean (default `False`) indicating if the resulting dictionary should be flattened. If it set to `True`, the 3 nested dictionaries (pytest status details, parameters, and optionally storages) will have their contents directly copied in the first level (with a prefix added in case of pytest status details).
 - **fixture_store**: a singleton or iterable containing dict-like fixture storage objects (see `@saved_fixture` and `create_results_bag_fixture`). If flatten=`False` the contents of these dictionaries will be added to the output in a dedicated 'fixtures' entry. If flatten=True all of their contents will be included directly.
 - **flatten_more**: a singleton, iterable or dictionary containing fixture names to flatten one level more in case flatten=True. If a dictionary is provided, the key should be the fixture name, and the value should be a prefix used for flattening its contents
 
**Returns**: a dictionary where the keys are pytest node ids. Each value is also a dictionary, containing information available from pytest concerning the test node, and optionally storage contents if `storage_dcts` is provided.


#### `filter_session_items(...)`

```python
filter_session_items(session,
                     filter=None,  # type: Any
                     )
```

Filters pytest session item in the provided `session`. An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test functions) and/or module names.
    
Used in [`get_session_synthesis_dct`](#get_session_synthesis_dct).

**Parameters**

 - **session**: a pytest session
 - **filter**: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use module names.

**Returns**: an iterable containing possibly filtered session items

#### `pytest_item_matches_filter(...)`

```python
pytest_item_matches_filter(item, filter)
```

Returns `True` if pytest session item `item` matches filter `filter`, `False` otherwise.

### d- Pytest utils

#### `get_all_pytest_fixture_names(...)`

```python
get_all_pytest_fixture_names(session,
                             filter=None,              # type: Any
                             filter_incomplete=False,  # type: bool
                             )
```

Returns the list of all unique fixture names used in all items in the provided session, with given filter.

An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test functions) and/or module names.

If this method is called before the end of the pytest session, some nodes might be incomplete, i.e. they will not have data for the three stages (setup/call/teardown). By default these nodes are filtered out but you can set `filter_incomplete=False` to make them appear. They will have a special 'pending' synthesis status.

**Parameters**

 - **session**: a pytest session object.
 - **filter**: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use modules.
 - **filter_incomplete**: a boolean indicating if incomplete nodes (without the three stages setup/call/teardown) should appear in the results (False) or not (True). Note: by default incomplete nodes DO APPEAR (this is different from get_session_synthesis_dct behaviour)

**Returns**: a list of fixture names corresponding to the desired filters

#### `get_all_pytest_param_names(...)`

```python
get_all_pytest_param_names(session,
                           filter=None,              # type: Any
                           filter_incomplete=False,  # type: bool
                           )
```

Returns the list of all unique parameter names used in all items in the provided session, with given filter.

An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test functions) and/or module names.

If this method is called before the end of the pytest session, some nodes might be incomplete, i.e. they will not have data for the three stages (setup/call/teardown). By default these nodes are filtered out but you can set `filter_incomplete=False` to make them appear. They will have a special 'pending' synthesis status.

**Parameters**

 - **session**: a pytest session object.
 - **filter**: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use modules.
 - **filter_incomplete**: a boolean indicating if incomplete nodes (without the three stages setup/call/teardown) should appear in the results (False) or not (True). Note: by default incomplete nodes DO APPEAR (this is different from get_session_synthesis_dct behaviour)

**Returns**: a list of parameter names corresponding to the desired filters

#### `get_fixture_value(...)`

`get_fixture_value(request, fixture_name)`

Returns the value associated with fixture named `fixture_name`, in provided `request` context. This is just an easy way to use `getfixturevalue` or `getfuncargvalue` according to whichever is available in current `pytest` version.


#### `get_pytest_status(...)`

`get_pytest_status(item, durations_in_ms=False, current_request=None)`

Returns a dictionary containing item's pytest status (success/skipped/failed, duration converted to ms) for
each pytest phase, and a tuple synthesizing the information.

The synthesis status contains the worst status of all phases (setup/call/teardown), or 'pending' if there are less than 3 phases.

The synthesis duration is equal to the duration of the 'call' phase (not to the sum of all phases: indeed, we are mostly interested in the test call itself).

**Parameters**

 - **item**: a pytest session.item
 - **durations_in_ms**: by default `pytest` measures durations in seconds so they are outputed in this unit. You can turn the flag to True to output milliseconds instead.
 - **current_request**: if a non-None `request` is provided and the item is precisely the one from the request, then the status will be 'pending'

**Returns**: a tuple ((test_status, test_duration), status_dct)

#### `is_pytest_incomplete(...)`

`is_pytest_incomplete(item)`

Returns `True` if a pytest item is incomplete - in other words if at least one of the 3 steps (setup/call/teardown) is missing from the available pytest report attached to this item.

#### `get_pytest_param_names(...)`

`get_pytest_param_names(item)`

Returns a list containing a pytest session item's parameters.

#### `get_pytest_params(...)`

Returns a dictionary containing a pytest session item's parameters.
