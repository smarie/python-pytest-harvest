# pytest-harvest

*Store data created during your `pytest` tests execution, and retrieve it at the end of the session, e.g. for applicative benchmarking purposes.*

[![Build Status](https://travis-ci.org/smarie/python-pytest-harvest.svg?branch=master)](https://travis-ci.org/smarie/python-pytest-harvest) [![Tests Status](https://smarie.github.io/python-pytest-harvest/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-pytest-harvest/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-pytest-harvest/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-pytest-harvest) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-pytest-harvest/) [![PyPI](https://img.shields.io/badge/PyPI-pytest_harvest-blue.svg)](https://pypi.python.org/pypi/pytest_harvest/)

`pytest` is a great tool to write test logic once and then generate multiple tests from *parameters*. Its *fixture* mechanism provides a cool way to inject dependencies in your tests.

At the end of a test session, you can already **collect various data** about the tests that have been run. However as opposed to *parameters* (`@pytest.mark.parametrize`), `pytest` purposedly does not keep *fixtures* (`@pytest.fixture`) in memory, because in general that would just be a waste of memory. Therefore you are currently **not able to retrieve fixture values at the end of the session**.

`pytest-harvest` allows you to very easily declare that a fixture should be stored in memory until the end of the session. This unlocks many new usages ; one of them proposed in this library is to create **special "result bag" fixtures** to collect interesting items from your tests.
 
For example you can now create **applicative benchmarks**. For example if you have a new data science algorithm and wish to run it against several datasets, you can 
 
 - create a *test* that applies the algorithm on a given dataset
 - *parametrize* it so that it runs against several datasets ([pytest-cases](https://smarie.github.io/python-pytest-cases/) might help you)
 - **NEW** store accuracy values in each test run thanks to a "result bag" *fixture*
 - **NEW** retrieve all accuracy values at the end of the *session* for reporting.

Note: you can learn more about how to design such a benchmark in [pytest-patterns](https://smarie.github.io/pytest-patterns/) (coming soon)

!!! note
    `pytest-harvest` has not yet been tested with pytest-xdist. See [#1](https://github.com/smarie/python-pytest-harvest/issues/1)

## Installing

```bash
> pip install pytest_harvest
```

## Usage

### Collecting tests status and parameters

Pytest already stores many information out of the box concerning tests that have run. You can easily retrieve them thanks to the `get_session_synthesis_dct(session)` utility function. For example let's assume you have this test:

```python
@pytest.mark.parametrize('p', ['hello', 'world'], ids=str)
def test_foo():
    print(p)
```


```python
from pytest_harvest import get_session_synthesis_dct
dct = get_session_synthesis_dct(request.session)
```


### Storing fixture values

You can either choose to store fixtures in a plain old variable, or in a session-scoped fixture. Both can be achieved using the same decorator `@saved_fixture(store)`.

#### Storing in a variable

Let's create a store. It should be a dict-like object:

```python
# Create a global store
STORE = dict()
```

In order to store fixture values in this object, simply decorate them with `@saved_fixture(store)`:

```python
from pytest
from pytest_harvest import saved_fixture

@pytest.fixture(params=[1, 2])
@saved_fixture(STORE)
def my_fix(request):
    """Each returned fixture value will be saved in the global store"""
    return request.param
``` 

Then you can have a look at the storage at the end of the pytest session with any of the standard means that pytest proposes to be called at session teardown or reporting stage. For example you can do it using a session-scoped fixture:

```python
@pytest.fixture(scope='session', autouse=True)
def register_final_test():
    print(dict(STORE['my_fix']))
```

or inside the "session end" hook in `conftest.py`:

```python
def pytest_sessionfinish(session, exitstatus):
    print(dict(STORE['my_fix']))
```

The result is an ordered dictionary where the keys are the test node ids, and the values are the fixture values:

```bash
{'pytest_harvest/tests_raw/test_saved_fixture_in_global_var.py::test_foo[1]': 1, 'pytest_harvest/tests_raw/test_saved_fixture_in_global_var.py::test_foo[2]': 2}
```

### Collecting test artifacts

Since the word "test results" might be misleading here (one could think about the standard success/failure results) we talk about test artifacts: we wish to collect objects that are created **within** the tests.
 
**TODO**

### Compliance with the other pytest mechanisms

This package solely relies on the fixtures mechanism. It should therefore be quite portable across pytest versions.

## Main features / benefits

 * **Store selected fixtures declaratively**: simply decorate your fixture with `@saved_fixture(storage)` and all fixture values will be stored in the selected storage
 * **Highly configurable**: storage object (for storing fixtures) or results bag object (for collecting results from tests) 

## See Also

 - [pytest documentation on parametrize](https://docs.pytest.org/en/latest/parametrize.html)
 - [pytest documentation on fixtures](https://docs.pytest.org/en/latest/fixture.html)
 - [pytest-patterns](https://smarie.github.io/pytest-patterns/), to go further and create for example a data science benchmark by combining this plugin with others.

### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-pytest-harvest](https://github.com/smarie/python-pytest-harvest)
