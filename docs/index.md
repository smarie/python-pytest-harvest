# pytest-harvest

*Store data created during your `pytest` tests execution, and retrieve it at the end of the session, e.g. for applicative benchmarking purposes.*

[![Build Status](https://travis-ci.org/smarie/python-pytest-harvest.svg?branch=master)](https://travis-ci.org/smarie/python-pytest-harvest) [![Tests Status](https://smarie.github.io/python-pytest-harvest/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-pytest-harvest/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-pytest-harvest/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-pytest-harvest) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-pytest-harvest/) [![PyPI](https://img.shields.io/badge/PyPI-pytest_harvest-blue.svg)](https://pypi.python.org/pypi/pytest_harvest/)

`pytest` is a great tool to write test logic once and then generate multiple tests from parameters. Its fixture mechanism provides a cool way to inject dependencies in your tests. As opposed to parameters (from `@pytest.mark.parametrize`), `pytest` purposedly **does not store** fixtures created during test execution, because in general that would just be a waste of memory. However for specific use-cases, users might wish to store them so as to access their values at the end of the session.

A very good example is if you use `pytest` to build data science benchmarks by running some algorithm against multiple cases. In that case you might be interested to

 - store accuracy values in each test run
 - retrieve all of them at the end of the session for reporting.

`pytest-harvest` has been designed just for that. Note: you can learn more about how to design such a benchmark in [pytest-patterns](https://smarie.github.io/pytest-patterns/)

!!! note
    `pytest-harvest` has not yet been tested with pytest-xdist. See [#7](https://github.com/smarie/python-pytest-harvest/issues/1)

## Installing

```bash
> pip install pytest_harvest
```

## Usage

### Storing fixture values

**TODO**

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
