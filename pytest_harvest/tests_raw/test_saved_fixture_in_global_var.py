# META
# {'passed': 2, 'failed': 0}
# END META

import os
import pytest

from collections import OrderedDict
from random import random

from pytest_harvest import saved_fixture
from pytest_harvest.common import yield_fixture

# init
this_file_name = os.path.split(__file__)[1]
unique_numbers = [random(), random()]


# The store is a global variable in this test
STORE = OrderedDict()


# Create our saved fixture, that will be saved in the global store
# -- 'normal' mode
@pytest.fixture(params=unique_numbers)
@saved_fixture(STORE)
def my_fix(request):
    # convert the parameter to a string so that the fixture is different from the parameter
    return str(request.param)


# -- 'generator' mode
@yield_fixture()
@saved_fixture(STORE)
def my_yield_fix():
    yield 12


def test_foo(my_fix, my_yield_fix):
    """"""
    print(my_fix)
    print(my_yield_fix)


# -----------------------------------------


def final_test(request):
    """This is the "test" that will be called when session ends. We check that the STORE contains everything"""
    for fixture_name, values in [('my_fix', [str(n) for n in unique_numbers]),
                                 ('my_yield_fix', [12, 12])]:
        assert fixture_name in STORE
        assert len(STORE[fixture_name]) == 2
        assert list(STORE[fixture_name].keys()) == [item.nodeid for item in request.session.items
                                                    if this_file_name in item.nodeid]
        assert list(STORE[fixture_name].values()) == values


@pytest.fixture(scope='session', autouse=True)
def register_final_test(request):
    # This is a way, compliant with legacy pytest 2.8, to register our teardown callback
    request.addfinalizer(lambda: final_test(request))
