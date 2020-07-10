# Advanced Usage

You have seen in the [introduction](./index.md) how to use the pre-wired fixtures to perform most comon tasks. The sections below explore, for each topic, the internals that are used behind the scenes, so that you are able to create custom behaviours if the default ones do not match your needs.

### 0- Prerequisite: how to write session teardown code

In order to be able to **retrieve** all the information that we will store, we will need to execute our retrieval/synthesis code **at the end of the entire test session**. 

`pytest` currently provides several ways to do this:

 * through a test (put it at the end of the latest test file to ensure execution at the end):

```python
def test_synthesis(request):
    # you can access the session from the injected 'request':
    session = request.session
    print("<Put here your synthesis code>")
```

 * through a generator (yield) session-scoped fixture (put this in any of your test files or in the `conftest.py` file):

```python
# Note: for pytest<3.0 you have to use @pytest.yield_fixture instead
@pytest.fixture(scope='session', autouse=True)
def my_cooler_session_finish(request):
    yield
    # you can access the session from the injected 'request':
    session = request.session
    print("<Put here your synthesis code>")
```

 * through a normal session-scoped fixture (put this in any of your test files or in the `conftest.py` file):
 
```python
@pytest.fixture(scope="session", autouse=True)
def my_session_finish(request):
    def _end():
        # you can access the session from the injected 'request':
        session = request.session
        print("<Put here your synthesis code>")
    request.addfinalizer(_end)
```

 * through the session finish [hook](https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_sessionfinish) (you have to write this function in the `conftest.py` file):

```python
def pytest_sessionfinish(session, exitstatus):
    print("<Put here your synthesis code>")
```

All seem completely equivalent for the usage of `pytest_harvest`. I personally prefer the "fixture" style because you can have several of them instead of a monolithic teardown hook. Besides they can be put in the test files so I typically put them as close as possible to the tests that store the data, so as to ensure maintainability (data creation/storage and data retrieval/synthesis code are in the same file).

### 1- Collecting tests status and parameters

Pytest already stores some information out of the box concerning tests that have run. In addition you can follow [this example](https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures) to retrieve more, but it requires you to write a hook so it is not very convenient. 

Instead, you can easily retrieve all of that thanks to the `get_session_synthesis_dct(session)` utility function. For example let's assume you have this parametrized test with a parametrized fixture:

```python
# unparametrized fixture
@pytest.fixture
def dummy():
    return "hey there !"

# parametrized fixture
@pytest.fixture(param=[1, 2])
def a_number_str(request):
    return "my_fix #%s" % request.param

# parametrized test using the fixtures
@pytest.mark.parametrize('p', ['hello', 'world'], ids=str)
def test_foo(p, a_number_str, dummy):
    print(p + a_number_str)
```

When running it, 4 tests are executed:

```bash
>>> pytest

============================= test session starts =============================
collected 4 items                                                              

path/to/test_file.py::test_foo[1-hello] PASSED [ 25%]
path/to/test_file.py::test_foo[1-world] PASSED [ 50%]
path/to/test_file.py::test_foo[2-hello] PASSED [ 75%]
path/to/test_file.py::test_foo[2-world] PASSED [100%]

========================== 4 passed in 0.11 seconds ===========================
```

let's retrieve the available information at the end of the session. The easiest way is to write a "last test" and make sure it is executed after all the other as shown below, but there are other ways as [shown above](#0-prerequisite-how-to-write-session-teardown-code):

```python
from pytest_harvest import get_session_synthesis_dct

def test_synthesis(request):
    synth_dct = get_session_synthesis_dct(request.session, status_details=True)
    print(dict(synth_dct))
```

It yields

```js
{
 'path/to/test_file.py::test_foo[1-hello]': {
            'pytest_duration': 0.0010001659393310547,
            'pytest_obj': <function test_foo at 0x0000000004C13B70>,
            'pytest_params': {'a_number_str_param': 1, 'p': 'hello'},
            'pytest_status': 'passed',
            'pytest_status_details': {'call': ('passed', 0.0010001659393310547),
                                      'setup': ('passed', 0.013001203536987305),
                                      'teardown': ('passed', 0.0)
                                     }
             },
 'path/to/test_file.py::test_foo[1-world]': {
            'pytest_duration': 0.0,
            'pytest_obj': <function test_foo at 0x0000000004C13B70>,
            'pytest_params': {'a_number_str_param': 1, 'p': 'world'},
            'pytest_status': 'passed',
            'pytest_status_details': {'call': ('passed', 0.0),
                                      'setup': ('passed', 0.0),
                                      'teardown': ('passed', 0.0)
                                     }
             },
 'path/to/test_file.py::test_foo[2-hello]': {
            'pytest_duration': 0.0010001659393310547,
            'pytest_obj': <function test_foo at 0x0000000004C13B70>,
            'pytest_params': {'a_number_str_param': 2, 'p': 'hello'},
            'pytest_status': 'passed',
            'pytest_status_details': {'call': ('passed', 0.0010001659393310547), 
                                      'setup': ('passed', 0.0010001659393310547),
                                      'teardown': ('passed', 0.0)
                                      }
             },
 'path/to/test_file.py::test_foo[2-world]': {
            'pytest_duration': 0.0,
            'pytest_obj': <function test_foo at 0x0000000004C13B70>,
            'pytest_params': {'a_number_str_param': 2, 'p': 'world'},
            'pytest_status': 'passed',
            'pytest_status_details': {'call': ('passed', 0.0),
                                      'setup': ('passed', 0.0010001659393310547),
                                      'teardown': ('passed', 0.0)
                                      }
            }
}
```

As you can see for each test node id you get a dictionary containing

 - `'pytest_obj'`the object containing the test code
 - `'pytest_status'` the status and `'pytest_duration'` the duration of the test
 - `'pytest_params'`the parameters used in this test (both in the test function AND the fixture)
 - `'pytest_status_details'` a dictionary containing the status details for each pytest internal stages: setup, call, and teardown. 
 
!!! note "status and duration aggregation" 
    that the global status corresponds to an aggregation of the status of each of those stages (setup, call, teardown), but the global duration is only the duration of the "call" stage - after all we do not care about how long it took to setup and teardown.

In addition, you can also use the following companion methods : 

 - `filter_session_items(session, filter=None)` is the filtering method used behind the scenes. `pytest_item_matches_filter` is the inner method used to test if a single item matches the filter.
 - `get_all_pytest_param_names(session)` lists all unique parameter names used, with optional filtering capabilities
 - `is_pytest_incomplete(item)`, `get_pytest_status(item)`, `get_pytest_param_names(item)` and `get_pytest_params(item)` can be used to analyse a specific item in `session.items` directly without creating the dictionary.

Finally let's have a closer look above. It **seems** that after all we have collected the fixtures, right ? For example we see `'a_number_str_param': 2`. But beware, this is not the fixture. It is the parameter used by the fixture `'a_number_str'`. To be convinced look at its type: it is an integer, not a string! A more obvious way to confirm that the fixtures are not available, is to see that the `'dummy'` fixture does not appear at all: indeed it had no parameters.

To conclude: the `get_session_synthesis_dct(session)` utility function allows you to collect many information about the tests, but not the fixtures. To do that you have to use the mechanisms below.

### 2- Storing/retrieving fixtures

You can either choose to store fixtures in a plain old variable, or in another, session-scoped, fixture. Both can be achieved using the same decorator `@saved_fixture(store)`.

#### a- Storing in a variable

Let's create a store. It should be a dict-like object:

```python
# Create a global store
STORE = dict()
```

In order to store all created fixture values in this object, simply decorate your fixture with `@saved_fixture(STORE)`:

```python
from pytest
from pytest_harvest import saved_fixture

@pytest.fixture(params=[1, 2])
@saved_fixture(STORE)
def my_fix(request):
    """Each returned fixture value will be saved in the global store"""
    return "my_fix #%s" % request.param
``` 

You can then retrieve the available information at the end of the session (put this in your [session teardown](#0-prerequisite-how-to-write-session-teardown-code)):

```python
print(dict(STORE['my_fix']))
```

Each saved fixture appears as an ordered dictionary stored under a global key that has its name (here 'my_fix'). In this dictionary, the keys are the test node ids, and the values are the fixture values:

```js
{'path/to/test_file.py::test_foo[1]': 'my_fix #1', 
'path/to/test_file.py::test_foo[2]': 'my_fix #2'}
```

Note: you can change the key used in the global storage with the `key=` argument of `@saved_fixture`. 

#### b- Storing in a fixture

You might want your store to be a fixture itself, instead of a global variable. It is possible if it is session- or module-scoped (in the same module than where it is used). Simply use its name in `@saved_fixture` and it will work as expected. 

This enables you to make the code even more readable because you can put the synthesis code in the teardown part of the storage fixture:

```python
from pytest
from pytest_harvest import saved_fixture

@pytest.fixture(params=[1, 2])
@saved_fixture("store")
def my_fix(request):
    """Each returned fixture value will be saved in the global store"""
    return "my_fix #%s" % request.param

# -- the global storage fixture and synthesis creator --
@pytest.fixture(scope='session', autouse=True)
def store():
    # setup: init the store
    store = OrderedDict()
    yield store
    # teardown: here you can collect all
    print(dict(store['my_fix']))
``` 

!!! note "other teardown hooks"
    If you use another teardown hook, you can still retrieve your `'store'` fixture by using the `get_fixture_value(request, 'store')` utility function provided in this library. 

!!! note "yield_fixture"
    In old versions of pytest, you have to use `@pytest.yield_fixture` to be allowed to use `yield` in a fixture.

### 3- Creating "results bags" fixtures to collect test artifacts

Now we are able to store fixtures. But what about the data that we create **during** the tests ? It can be accuracy results, etc.

For this, simply use `create_results_bag_fixture()` to create "results bags" fixtures where you can put any data you want:
 
```python
from collections import OrderedDict
from random import random
import pytest
from pytest_harvest import create_results_bag_fixture

def my_algorithm(param, data):
    # let's return a random accuracy !
    return random()

@pytest.fixture(params=['A', 'B', 'C'])
def dataset(request):
    return "my dataset #%s" % request.param

@pytest.mark.parametrize("algo_param", [1, 2], ids=str)
def test_my_app_bench(algo_param, dataset, results_bag):
    """
    This test applies the algorithm with various parameters (`algo_param`)
    on various datasets (`dataset`). Accuracies are stored in a results
    bag (`results_bag`)
    """
    # apply the algorithm with param `algo_param` on dataset `dataset`
    accuracy = my_algorithm(algo_param, dataset)
    # store it in the results bag
    results_bag.accuracy = accuracy

# -- the results bag fixture --
# note: depending on your pytest version, the name used by pytest might be
# the variable name (left) or the one you provide in the 'name' argument so 
# make sure they are identical! 
results_bag = create_results_bag_fixture('store', name="results_bag")

# -- the global storage fixture and synthesis creator --
@pytest.fixture(scope='session', autouse=True)
def store(request):
    # setup: init the store
    store = OrderedDict()
    yield store
    # teardown: here you can collect all
    print(dict(store['results_bag']))
```

We can see the correct results collected:

```js
{
'path/to/test_file.py::::test_my_app_bench[A-1]': 
     ResultsBag: {'accuracy': 0.2630766637159053}, 
'path/to/test_file.py::::test_my_app_bench[A-2]': 
     ResultsBag: {'accuracy': 0.6720533462346249}, 
'path/to/test_file.py::::test_my_app_bench[B-1]':
     ResultsBag: {'accuracy': 0.9121353916881674}, 
'path/to/test_file.py::::test_my_app_bench[B-2]': 
     ResultsBag: {'accuracy': 0.9401074040573346}, 
'path/to/test_file.py::::test_my_app_bench[C-1]': 
     ResultsBag: {'accuracy': 0.01619034700438804},
'path/to/test_file.py::::test_my_app_bench[C-2]': 
     ResultsBag: {'accuracy': 0.8027244886806986}
}
```

We can of course combine this with the test status and parameters (we saw [above](#1-collecting-tests-status-and-parameters) how to collect them) if we want to create a synthesis table. This complete story will be available on [pytest-patterns](https://github.com/smarie/pytest-patterns).

!!! note "results bag fixtures' storage"
    You declare the storage used in the arguments of `create_results_bag_fixture`. As this relies on `@saved_fixture`, you can use both a variable or a session/module-scoped fixture name as we saw in previous chapter. 

### 4- Creating a Synthesis table

Now that we know

 - how to retrieve pytest status and parameters
 - how to store and retrieve fixtures
 - and how to store and retrieve applicative results

We can create a synthesis table containing all information available. This is very easy: instead of calling `get_session_synthesis_dct` with no parameters, give it your `store` object. Since we want to create a table, we will use the `flatten` and `flatten_more` options so that the result does not contain nested dictionaries for the parameters, fixtures, and result bags. Finally we decide that we want the durations expressed in ms (pytest measures them in seconds by default).

```python
# retrieve the synthesis, merged with the fixture store
results_dct = get_session_synthesis_dct(session, fixture_store=store, 
                                        flatten=True, flatten_more='results_bag',
                                        durations_in_ms=True)
```

We can print the first entry:

```python
>>> pprint(dict(next(iter(results_dct.values()))))

{'pytest_obj': <function test_my_app_bench at 0x0000000004FF6A60>,
 'pytest_status': 'passed',
 'pytest_duration_ms': 0.0,
 'dataset': 'A',
 'algo_param': 1,
 'accuracy': 0.2630766637159053}
```

We see that all information is available at the same level: pytest status and duration, parameters (`dataset` and `algo_param`), and results (`accuracy`).

Transforming such a flattened dictionary in a table is very easy with `pandas`:

```python
import pandas as pd
results_df = pd.DataFrame.from_dict(results_dct, orient='index')
# (a) remove the full test id path
results_df.index = results_df.index.to_series() \
                             .apply(lambda test_id: test_id.split('::')[-1])
# (b) drop pytest object column
results_df.drop(['pytest_obj'], axis=1, inplace=True)
```

And finally we can use `pandas` or `tabulate` to export the result in csv or markdown format:

```python
# csv format
print(results_df.to_csv())

# github markdown format
from tabulate import tabulate
print(tabulate(results_df, headers='keys'))
```

|                        | status   |   duration_ms |   algo_param | dataset   |   accuracy |
|------------------------|----------|---------------|--------------|-----------|------------|
| test_my_app_bench[A-1] | passed   |       1.00017 |            1 | A         |  0.313807  |
| test_my_app_bench[A-2] | passed   |       0       |            2 | A         |  0.0459802 |
| test_my_app_bench[B-1] | passed   |       0       |            1 | B         |  0.638511  |
| test_my_app_bench[B-2] | passed   |       0       |            2 | B         |  0.10418   |
| test_my_app_bench[C-1] | passed   |       0       |            1 | C         |  0.287151  |
| test_my_app_bench[C-2] | passed   |       0       |            2 | C         |  0.19437   |

!!! note "Duration calculation"
    The duration field is directly extracted from `pytest`. Before version 6, `pytest` computed durations using the `time` method, which was not as accurate as other methods. From [version 6 on, it uses `perf_counter()`](https://docs.pytest.org/en/latest/changelog.html#pytest-6-0-0rc1-2020-07-08) ([pytest#4391](https://github.com/pytest-dev/pytest/issues/4391) was fixed). If you need to measure the duration of a specific sub-function instead of the duration of the whole test function call, use [pytest-benchmark](https://github.com/ionelmc/pytest-benchmark).

### 5- Partial synthesis (module, function) and synthesis tests

We have seen [above](#1-collecting-tests-status-and-parameters) that you can get the pytest `session` object from many different teardown hooks. In addition, you can even access it from inside a test! In that case all information will not be available, but if the synthesis test is located **after** the test function of interest in execution order, it will be ok.

To be sure to only get results you're interested in, the special `filter` argument allows you to only select parts of the test nodes to create the synthesis:

```python
# a module-scoped store
@pytest.fixture(scope='module', autouse=True)
def store():
    return OrderedDict()

# results bag fixture
my_results = create_results_bag_fixture('store', name='my_results')

def test_foo(my_results):
    ...

def test_synthesis(request, store):
    # get partial results concerning `test_foo`
    results_dct = get_session_synthesis_dct(request.session, filter=test_foo, 
                                            fixture_store=store)
    
    # you can assert / report using the `results_dct` here
```

See `help(get_session_synthesis_dct)` for details: for example you can include in this filter a list, and it can contain module names too.

### Complete example

A module-scoped complete example with parameters, fixtures, and results bag can be found in two versions:
 
 - [here](https://github.com/smarie/python-pytest-harvest/tree/master/pytest_harvest/tests/test_doc_example.py) with no customization (leveraging the default fixtures)
 - [here](https://github.com/smarie/python-pytest-harvest/tree/master/pytest_harvest/tests/test_doc_example_custom.py) to perform the exact same behaviour but with custom store and results bag.
