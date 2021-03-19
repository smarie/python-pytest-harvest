# pytest-harvest

*Store data created during your `pytest` tests execution, and retrieve it at the end of the session, e.g. for applicative benchmarking purposes.*

[![Python versions](https://img.shields.io/pypi/pyversions/pytest-harvest.svg)](https://pypi.python.org/pypi/pytest-harvest/) [![Build Status](https://github.com/smarie/python-pytest-harvest/actions/workflows/base.yml/badge.svg)](https://github.com/smarie/python-pytest-harvest/actions/workflows/base.yml) [![Tests Status](https://smarie.github.io/python-pytest-harvest/reports/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-pytest-harvest/reports/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-pytest-harvest/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-pytest-harvest)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-pytest-harvest/) [![PyPI](https://img.shields.io/pypi/v/pytest-harvest.svg)](https://pypi.python.org/pypi/pytest-harvest/) [![Downloads](https://pepy.tech/badge/pytest-harvest)](https://pepy.tech/project/pytest-harvest) [![Downloads per week](https://pepy.tech/badge/pytest-harvest/week)](https://pepy.tech/project/pytest-harvest) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-pytest-harvest.svg)](https://github.com/smarie/python-pytest-harvest/stargazers)

!!! success "now compliant with `pytest-xdist`! [check it out](#pytest-x-dist)"

`pytest` is a great tool to write test logic once and then generate multiple tests from *parameters*. Its *fixture* mechanism provides a cool way to inject dependencies in your tests.

At the end of a test session, you can already **collect various data** about the tests that have been run. But it is a bit cumbersome to get it right, and requires you to write a plugin (see [this advice](https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures)).

Besides, as opposed to *parameters* (`@pytest.mark.parametrize`), `pytest` purposedly does not keep *fixtures* (`@pytest.fixture`) in memory, because in general that would just be a waste of memory. Therefore you are currently **not able to retrieve fixture values at the end of the session**.

Finally, what about other kind of **applicative results** that you produce during test execution ? There is no current mechanism in `pytest` to manage that.

With `pytest-harvest`:

 * you can **store all instances of a fixture** with `@saved_fixture`, so that they remain available until the end of the test session. If you're only interested in some aspects of the fixture, you can store "*views*" instead.
 
 * you can use the special `results_bag` fixture to **collect interesting results** within your tests.
 
 * you can use the special `[session/module]_results_[dct/df]` fixtures to easily **collect all available data** at the end of a session or module, without having to register `pytest` hooks. The status, duration and parameters of all tests become easily available both as dictionary or `pandas` dataframe, and your saved fixtures and results are there too. 
 
 * you can create your own variants of the above thanks to the API, for more customized data collection and synthesis.

 
With all that, you can now easily create **applicative benchmarks**. See [pytest-patterns](https://smarie.github.io/pytest-patterns/) for an example of data science benchmark.


## Installing

```bash
> pip install pytest_harvest
```

## Usage

### a- Collecting fixture instances

Simply use the `@saved_fixture` decorator on your fixtures to declare that their instances must be saved. By default they are saved in a session-scoped `fixture_store` fixture that you can therefore grab and inspect in other tests or in any compliant pytest entry point:

```python
import pytest
from pytest_harvest import saved_fixture

@pytest.fixture(params=range(2))
@saved_fixture
def person(request):
    """
    A dummy fixture, parametrized so that it has two instances
    """
    if request.param == 0:
        return "world"
    elif request.param == 1:
        return "self"

def test_foo(person):
    """
    A dummy test, executed for each `person` fixture available
    """
    print('\n   hello, ' + person + ' !')

def test_synthesis(fixture_store):
    """
    In this test we inspect the contents of the fixture store so far,
    and check that the 'person' entry contains a dict <test_id>: <person>
    """
    # print the keys in the store
    print("\n   Available `fixture_store` keys:")
    for k in fixture_store:
        print("    - '%s'" % k)

    # print what is available for the 'person' entry
    print("\n   Contents of `fixture_store['person']`:")
    for k, v in fixture_store['person'].items():
        print("    - '%s': %s" % (k, v))
```

Let's execute it:

```bash
>>> pytest -s -v

============================= test session starts =============================
...
collecting ... collected 3 items
test_doc_basic_saved_fixture.py::test_foo[0] 
   hello, world !
PASSED
test_doc_basic_saved_fixture.py::test_foo[1] 
   hello, self !
PASSED
test_doc_basic_saved_fixture.py::test_synthesis 
   Available `fixture_store` keys:
    - 'person'

   Contents of `fixture_store['person']`:
    - 'test_doc_basic_saved_fixture.py::test_foo[0]': world
    - 'test_doc_basic_saved_fixture.py::test_foo[1]': self
PASSED

========================== 3 passed in 0.09 seconds ===========================
```

As you can see, the `fixture_store` contains one entry for each saved fixture, and this entry's value is a dictionary of `{<test_id>: <fixture_value>}`.  We will see [below](#d-collecting-all-at-once) how to combine this information with information already available in pytest (test status, duration...).

#### Collecting fixture views

Sometimes you are not interested in storing the whole fixture but maybe just some aspect of it. For example maybe the fixture is a huge dataset, and you just wish to remember a few characteristics about it.

Simply use the `views=` argument in `@saved_fixture` to save views instead of the fixture itself. That argument should contain a dictionary of `{<view_key>: <view_creation_function>}`.

In the previous example if we only want to save the first and last character of the `person` fixture, we can do:

```python
@pytest.fixture(params=range(2))
@saved_fixture(views={'person_initial': lambda p: p[0], 
                      'person_last_char': lambda p: p[-1]})
def person(request):
    """
    A dummy fixture, parametrized so that it has two instances
    """
    if request.param == 0:
        return "world"
    elif request.param == 1:
        return "self"
```

The fixture store will then contain as many entries as there are views.

### b- Collecting test artifacts

Simply use the `results_bag` fixture in your tests and you'll be able to store items in it. This object behaves like a munch: if you create/read a field it will create/read a dictionary entry. By default the `results_bag` fixture is stored in the `fixture_store` so you can retrieve it at the end as shown previously.

```python
from datetime import datetime
import pytest

@pytest.mark.parametrize('p', ['world', 'self'], ids=str)
def test_foo(p, results_bag):
    """
    A dummy test, parametrized so that it is executed twice
    """
    print('\n   hello, ' + p + ' !')

    # Let's store some things in the results bag
    results_bag.nb_letters = len(p)
    results_bag.current_time = datetime.now().isoformat()

def test_synthesis(fixture_store):
    """
    In this test we inspect the contents of the fixture store so far, and 
    check that the 'results_bag' entry contains a dict <test_id>: <results_bag>
    """
    # print the keys in the store
    print("\n   Available `fixture_store` keys:")
    for k in fixture_store:
        print("    - '%s'" % k)

    # print what is available for the 'results_bag' entry
    print("\n   Contents of `fixture_store['results_bag']`:")
    for k, v in fixture_store['results_bag'].items():
        print("    - '%s':" % k)
        for kk, vv in v.items():
            print("      - '%s': %s" % (kk, vv))
```

Let's execute it:

```bash
>>> pytest -s -v

============================= test session starts =============================
...
collecting ... collected 3 items
test_doc_basic_results_bag.py::test_foo[world] 
   hello, world !
PASSED
test_doc_basic_results_bag.py::test_foo[self] 
   hello, self !
PASSED
test_doc_basic_results_bag.py::test_synthesis 
   Available `fixture_store` keys:
    - 'results_bag'

   Contents of `fixture_store['results_bag']`:
    - 'test_doc_basic_results_bag.py::test_foo[world]':
      - 'nb_letters': 5
      - 'current_time': 2018-12-08T22:20:10.695791
    - 'test_doc_basic_results_bag.py::test_foo[self]':
      - 'nb_letters': 4
      - 'current_time': 2018-12-08T22:20:10.700791
PASSED

========================== 3 passed in 0.05 seconds ===========================
```

As in previous example, the `fixture_store` contains one entry for `'results_bag'`, and this entry's value is a dictionary of `{<test_id>: <results_bag>}`. We can therefore access all values stored within each test (here, `nb_letters` and `current_time`). 

We will see [below](#d-collecting-all-at-once) how to combine this information with information already available in pytest.

### c- Collecting a synthesis

**as a** `dict`

Simply use the `module_results_dct` fixture to get a dictionary containing the test results *in that module*, *so far*. You can use this fixture in a test as shown below (`test_synthesis`) or in any compliant pytest entry point. 

```python
import pytest
import time

@pytest.mark.parametrize('p', ['world', 'self'], ids=str)
def test_foo(p):
    """
    A dummy test, parametrized so that it is executed twice
    """
    print('\n   hello, ' + p + ' !')
    time.sleep(len(p) / 10)
    
def test_synthesis(module_results_dct):
    """
    In this test we just look at the synthesis of all tests 
    executed before it, in that module.
    """
    # print the keys in the synthesis dictionary
    print("\n   Available `module_results_dct` keys:")
    for k in module_results_dct:
        print("    - " + k)

    # print what is available for a single test
    print("\n   Contents of 'test_foo[world]':")
    for k, v in module_results_dct['test_foo[world]'].items():
        if k != 'status_details':
            print("    - '%s': %s" % (k, v))
        else:
            print("    - '%s':" % k)
            for kk, vv in v.items():
                print("      - '%s': %s" % (kk, vv))
```

Let's execute it:

```bash
>>> pytest -s -v

============================= test session starts =============================
...
collecting ... collected 3 items
test_doc_basic.py::test_foo[world]
   hello, world !
PASSED
test_doc_basic.py::test_foo[self]
   hello, self !
PASSED
test_doc_basic.py::test_synthesis 
   Available `module_results_dct` keys:
    - test_foo[world]
    - test_foo[self]

   Contents of 'test_foo[world]':
    - 'pytest_obj': <function test_foo at 0x0000000005A7DEA0>
    - 'status': passed
    - 'duration_ms': 500.0283718109131
    - 'status_details':
      - 'setup': ('passed', 3.0002593994140625)
      - 'call': ('passed', 500.0283718109131)
      - 'teardown': ('passed', 2.0003318786621094)
    - 'params': OrderedDict([('p', 'world')])
    - 'fixtures': OrderedDict()
PASSED

========================== 3 passed in 0.05 seconds ===========================
```

As you can see, for each test node id you get a dictionary containing

 - `'pytest_obj'`the object containing the test code
 - `'status'` the status of the test (passed/skipped/failed)
 - `'duration_ms'` the duration of the test as measured by pytest (only the "call" step is measured here, not setup nor teardown times)
 - `'status_details'`: details (status and duration) for each pytest phase
 - `'params'`the parameters used in this test (both in the test function AND the fixtures)
 - `'fixtures'` the saved fixture instances (not parameters) for this test. Here we see the saved fixtures and result bags, if any (see [below](#d-collecting-all-at-once) for a complete example) 

Note: if you need the synthesis to contain all tests of the *session* instead of just the current *module*, use fixture `session_results_dct` instead.


**as a** `DataFrame`

Simply use the `module_results_df` fixture instead of `module_results_dct` (note the `df` suffix instead of `dct`) to get the same contents as a table, which might be more convenient for statistics and aggregations of all sorts. Note: you have to have `pandas` installed for this fixture to be available.

Replacing the above `test_synthesis` function with 

```python
def test_synthesis(module_results_df):
    """
    In this variant we use the 'dataframe' fixture
    """
    # print the synthesis dataframe
    print("\n   `module_results_df` dataframe:\n")
    print(module_results_df)
```

yields:

```bash
>>> pytest -s -v

============================= test session starts =============================
...
collecting ... collected 3 items
test_doc_basic.py::test_foo[world] 
   hello, world !
PASSED
test_doc_basic.py::test_foo[self] 
   hello, self !
PASSED
test_doc_basic.py::test_synthesis 
   `module_results_df` dataframe:
   
                 status  duration_ms      p
test_id                                    
test_foo[world]  passed   500.028610  world
test_foo[self]   passed   400.022745   self
PASSED

========================== 3 passed in 0.05 seconds ===========================
```

As can be seen above, each row in the dataframe corresponds to a test (the index is the test id), and the various information are presented in columns. As opposed to the dictionary version, status details are not provided.

Note: as for the dict version, if you need the synthesis to contain all tests of the *session* instead of just the current *module*, use fixture `session_results_df` instead.

### d- collecting all at once

We have seen first how to collect *saved fixtures*, and *test artifacts* thanks to results bags. Then we saw how to collect *pytest status and duration information, as well as parameters*. 

You may now wonder how to collect all of this in a single handy object ? Well, the answer is quite simple: you have nothing more to do. Indeed, the `[module/session]_results_[dct/df]` fixtures that we saw in previous chapter will by default contain *all* saved fixtures and results bags. 

Let's try it:

```python
import time
from datetime import datetime
from tabulate import tabulate

import pytest
from pytest_harvest import saved_fixture

@pytest.fixture(params=range(2))
@saved_fixture
def person(request):
    """
    A dummy fixture, parametrized so that it has two instances
    """
    if request.param == 0:
        return "world"
    elif request.param == 1:
        return "self"

@pytest.mark.parametrize('double_sleep_time', [False, True], ids=str)
def test_foo(double_sleep_time, person, results_bag):
    """
    A dummy test, parametrized so that it is executed twice.
    """
    print('\n   hello, ' + person + ' !')
    time.sleep(len(person) / 10 * (2 if double_sleep_time else 1))

    # Let's store some things in the results bag
    results_bag.nb_letters = len(person)
    results_bag.current_time = datetime.now().isoformat()

def test_synthesis(module_results_df):
    """
    In this test we just look at the synthesis of all tests
    executed before it, in that module.
    """
    # print the synthesis dataframe
    print("\n   `module_results_df` dataframe:\n")
    
    # we use 'tabulate' for a nicer output format
    print(tabulate(module_results_df, headers='keys', tablefmt="pipe"))
```

yields

```bash
>>> pytest -s -v

============================= test session starts =============================
...
collecting ... collected 5 items
test_doc_basic_df_all.py::test_foo[0-False] 
test_doc_basic_df_all.py::test_foo[0-True] 
test_doc_basic_df_all.py::test_foo[1-False] 
test_doc_basic_df_all.py::test_foo[1-True] 
test_doc_basic_df_all.py::test_synthesis 
   hello, world !
PASSED
   hello, world !
PASSED
   hello, self !
PASSED
   hello, self !
PASSED
   `module_results_df` dataframe:

| test_id           | pytest_obj                                | status   |   duration_ms | double_sleep_time   |   person_param | person   |   nb_letters | current_time               |
|:------------------|:------------------------------------------|:---------|--------------:|:--------------------|---------------:|:---------|-------------:|:---------------------------|
| test_foo[0-False] | <function test_foo at 0x0000000004F8C488> | passed   |       500.029 | False               |              0 | world    |            5 | 2018-12-10T22:06:32.279561 |
| test_foo[0-True]  | <function test_foo at 0x0000000004F8C488> | passed   |      1000.06  | True                |              0 | world    |            5 | 2018-12-10T22:06:33.283618 |
| test_foo[1-False] | <function test_foo at 0x0000000004F8C488> | passed   |       400.023 | False               |              1 | self     |            4 | 2018-12-10T22:06:33.687641 |
| test_foo[1-True]  | <function test_foo at 0x0000000004F8C488> | passed   |       800.046 | True                |              1 | self     |            4 | 2018-12-10T22:06:34.491687 |
PASSED

========================== 5 passed in 3.87 seconds ===========================
```

So we see here that we get all the information in a single handy table object: for each test, we get its status, duration, parameters (`double_sleep_time`, `person_param`), fixtures (`person`) and results (`nb_letters`, `current_time`).

Of course you can still get the same information as a dictionary, and chose to get it for the whole session or for a specific module (see previous [chapter](#c-collecting-a-synthesis)). 

### e- advanced usage

All the behaviours described above are pre-wired using fixtures, to help most users getting started. For each fixture described above there is an equivalent method in `pytest-harvest` [API](./api_reference.md#associated-getter-functions), so that you may access the same information from within a pytest hook such as `pytest_sessionfinish(session)`:

 * `fixture_store` fixture: `get_fixture_store(session)`
 * `module_results_dct` fixture: `get_module_results_dct(session, module_name)`
 * `module_results_df` fixture: `get_module_results_df(session, module_name)`
 * `session_results_dct` fixture: `get_session_results_dct(session)`
 * `session_results_df` fixture: `get_session_results_df(session)`

Finally, these fixtures and equivalent methods are nothing but pre-wiring of more generic capabilities, that are offered in this library as well. So if these pre-wired objects do not suit your needs and you wish to create **custom synthesis**, **custom store objects**, **custom results bags**... see [advanced usage page](./advanced_usage).


## Compliance with the pytest ecosystem

This plugin mostly relies on the fixtures mechanism and the `pytest_runtest_makereport` hook. It should therefore be quite portable across pytest versions (at least it is tested against pytest 2, 3, 4, 5, for both python 2 and 3).

### pytest x-dist 

You may wish to rely on `pytest-xdist` to parallelize/distribute your tests. In that case, you can not rely on the `[module/session]_results_[dct/df]` fixtures described previously to collect your synthesis because as of today there is no way to ensure that these methods will run last on the workers, and to run them at all on the master. So instead of using these fixtures, simply use the equivalent methods `get_[module/session]_results_[dct/df](session, [module_name])` in a pytest hook, and `pytest-harvest` will take care of the rest.

More precisely, when `pytest-xdist` is used to distribute tests, worker node results are automatically stored by `pytest-harvest` in a file at the end of their respective pytest session using pickle, in a temporary `.xdist_harvested/` folder. These results are automatically retrieved and consolidated when any of the `get_[module/session]_results_[dct/df]` method is called from the master node. Finally, the temporary folder is deleted at the end of master node session. You can use the `get_[module/session]_results_[dct/df]` methods in any pytest hook on the "master" node, for example in the `pytest_sessionfinish` hook. The methods continue to work on worker nodes, so to know if you are in the master node, a `is_main_process` function is provided.

Below is an example of `conftest.py` that works both *with* and *without* `pytest-xdist` enabled, and within both master an worker nodes:

```python
from pytest_harvest import is_main_process, get_xdist_worker_id, \
                           get_session_results_df

def pytest_sessionfinish(session):
    """ Gather all results and save them to a csv. 
    Works both on worker and master nodes, and also with xdist disabled"""

    session_results_df = get_session_results_df(session)
    suffix = 'all' if is_main_process(session) else get_xdist_worker_id(session)
    session_results_df.to_csv('results_%s.csv' % suffix)
```

Note: you can also do the persist/restore operation yourself using the hooks provided. See [`newhooks`](https://github.com/smarie/python-pytest-harvest/blob/master/pytest_harvest/newhooks.py) for details. Below is a `contest.py` example doing the same than the default behaviour, but with a different temporary folder:

```python
from pathlib import Path
from shutil import rmtree
import pickle
from logging import warning

# Define the folder in which temporary worker's results will be stored
RESULTS_PATH = Path('./.xdist_results/')
RESULTS_PATH.mkdir(exist_ok=True)

def pytest_harvest_xdist_init():
    # reset the recipient folder
    if RESULTS_PATH.exists():
        rmtree(RESULTS_PATH)
    RESULTS_PATH.mkdir(exist_ok=False)
    return True

def pytest_harvest_xdist_worker_dump(worker_id, session_items, fixture_store):
    # persist session_items and fixture_store in the file system
    with open(RESULTS_PATH / ('%s.pkl' % worker_id), 'wb') as f:
        try:
            pickle.dump((session_items, fixture_store), f)
        except Exception as e:
            warning("Error while pickling worker %s's harvested results: " 
                    "[%s] %s", (worker_id, e.__class__, e))
    return True

def pytest_harvest_xdist_load():
    # restore the saved objects from file system
    workers_saved_material = dict()
    for pkl_file in RESULTS_PATH.glob('*.pkl'):
        wid = pkl_file.stem
        with pkl_file.open('rb') as f:
            workers_saved_material[wid] = pickle.load(f)
    return workers_saved_material

def pytest_harvest_xdist_cleanup():
    # delete all temporary pickle files
    rmtree(RESULTS_PATH)
    return True
```

## Main features / benefits

 * **Collect test execution information easily**: with the default `[module/session]_results_[dct/df]` fixtures, and with `get_session_synthesis_dct(session)` (advanced users), you can collect all the information you need, without the hassle of writing hooks. 

 * **Store selected fixtures declaratively**: simply decorate your fixture with `@saved_fixture` and all fixture values will be stored in the default storage. You can use the advanced `@saved_fixture(store)` to customize the storage (a variable or another fixture).
 
 * **Collect test artifacts**: simply use the `results_bag` fixture to start collecting results from your tests. You can also create your own "results bags" fixtures (advanced). It makes it very easy to create applicative benchmarks, for example for [data science](https://smarie.github.io/pytest-patterns/).
 
 * **Highly configurable**: storage object (for storing fixtures) or results bag objects (for collecting results from tests) can be of any object type of your choice. For results bags, a default type is provided that behaves like a "munch" (both a dictionary and an object). See [advanced usage page](./advanced_usage).

## See Also

 - [pytest documentation on parametrize](https://docs.pytest.org/en/latest/parametrize.html)
 - [pytest documentation on fixtures](https://docs.pytest.org/en/latest/fixture.html)
 - [pytest-patterns](https://smarie.github.io/pytest-patterns/), to go further and create for example a data science benchmark by combining this plugin with others.

### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-pytest-harvest](https://github.com/smarie/python-pytest-harvest)
