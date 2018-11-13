# META
# {'passed': 2, 'failed': 0}
# END META

import os
import pytest

from collections import OrderedDict
from random import random

from pytest_harvest import saved_fixture, get_fixture_value
from pytest_harvest.common import yield_fixture


# init
this_file_name = os.path.split(__file__)[1]
unique_numbers = [random(), random()]


@pytest.fixture(params=unique_numbers)
@saved_fixture('store')
def my_fix(request):
    """Our saved fixture, that will be saved in the store fixture"""
    # convert the parameter to a string so that the fixture is different from the parameter
    return "my_fix #%s" % request.param


def test_foo(my_fix):
    """"""
    print(my_fix)


# -----------------------------------------


@yield_fixture(scope='session', autouse=True)
def store(request):

    # yield the store fixture
    store = OrderedDict()
    yield store

    # check that this util works
    assert get_fixture_value(request, 'store') == store

    # check that the store contains everything
    assert 'my_fix' in store
    assert len(store['my_fix']) == 2
    assert list(store['my_fix'].keys()) == [item.nodeid for item in request.session.items
                                            if this_file_name in item.nodeid]
    assert list(store['my_fix'].values()) == [("my_fix #%s" % n) for n in unique_numbers]
