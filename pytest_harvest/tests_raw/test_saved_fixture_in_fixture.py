# META
# {'passed': 2, 'failed': 0}
# END META

import os
import pytest

from collections import OrderedDict
from random import random

from pytest_harvest import saved_fixture, get_fixture_value


# init
this_file_name = os.path.split(__file__)[1]
unique_numbers = [random(), random()]


@pytest.fixture(params=unique_numbers)
@saved_fixture('store')
def my_fix(request):
    """Our saved fixture, that will be saved in the store fixture"""
    return request.param


def test_foo(my_fix):
    """"""
    print(my_fix)


# -----------------------------------------


def final_test(request):
    """This is the "test" that will be called when session ends. We check that the STORE contains everything"""

    # retrieve the store fixture
    store = get_fixture_value(request, 'store')

    assert 'my_fix' in store
    assert len(store['my_fix']) == 2
    assert list(store['my_fix'].keys()) == [item.nodeid for item in request.session.items
                                            if this_file_name in item.nodeid]
    assert list(store['my_fix'].values()) == unique_numbers


@pytest.fixture(scope='session', autouse=True)
def store(request):

    # initialize the store
    store_obj = OrderedDict()

    # This is a way, compliant with legacy pytest 2.8, to register a teardown callback on the store fixture
    request.addfinalizer(lambda: final_test(request))

    # provide the store object fixture
    return store_obj
