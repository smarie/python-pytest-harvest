# META
# {'passed': 3, 'failed': 0}
# END META
from collections import OrderedDict

import pytest
from pytest_harvest import saved_fixture, filter_session_items

my_store = OrderedDict()


@pytest.fixture(scope='session')
@saved_fixture(store=my_store)
def my_fix():
    return 1


@pytest.fixture(scope='module')
@saved_fixture(store=my_store)
def my_fix2():
    return 1


def test_foo(my_fix):
    assert my_fix == 1


def test_bar(my_fix, my_fix2):
    assert my_fix == 1


def test_synthesis(request):
    fixture_store = my_store

    # the first is used by the first test: it appears for it and then does not re-appear (not re-created)
    print(dict(fixture_store['my_fix']))
    prefix = get_prefix(request, test_synthesis)
    assert list(fixture_store['my_fix'].keys()) == ['%s::test_foo' % prefix]

    # the second only appears when created
    print(dict(fixture_store['my_fix2']))
    assert list(fixture_store['my_fix2'].keys()) == ['%s::test_bar' % prefix]


def get_prefix(request, test_func):
    """
    Utility method to return the prefix to use for node ids, that will work whatever the invocation method.
    If this is not used the test might work when executed in "raw" mode, but might hang when executed using the
    "pytester" plugin (from tests/test_all_raw_with_meta_check)

    :param request:
    :param test_func:
    :return:
    """
    items = filter_session_items(request.session, filter=test_func.__module__)
    last_node_id = items[-1].nodeid
    prefix = last_node_id.split('::')[0]
    return prefix
