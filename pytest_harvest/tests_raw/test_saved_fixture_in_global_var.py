# META
# {'passed': 2, 'failed': 0}
# END META

import os
import pytest

from collections import OrderedDict
from random import random

from pytest_harvest import saved_fixture


# init
this_file_name = os.path.split(__file__)[1]
unique_numbers = [random(), random()]


# The store is a global variable in this test
STORE = OrderedDict()


@saved_fixture(STORE)
@pytest.fixture(params=unique_numbers)
def my_fix(request):
    """Our saved fixture, that will be saved in the global store"""
    return request.param


def test_foo(my_fix):
    """"""
    print(my_fix)


# -----------------------------------------


def final_test(request):
    """This is the "test" that will be called when session ends. We check that the STORE contains everything"""
    assert 'my_fix' in STORE
    assert list(STORE['my_fix'].keys()) == [item.nodeid for item in request.session.items
                                            if this_file_name in item.nodeid]
    assert list(STORE['my_fix'].values()) == unique_numbers


@pytest.fixture(scope='session', autouse=True)
def register_final_test(request):
    # This is a way, compliant with legacy pytest 2.8, to register our teardown callback
    request.addfinalizer(lambda: final_test(request))
