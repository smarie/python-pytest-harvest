# META
# {'passed': 7, 'failed': 0}
# END META

import pytest
from pytest_harvest import saved_fixture, filter_session_items


@pytest.fixture(scope='module', params=[1, 2])
@saved_fixture
def my_fix():
    return 1


@pytest.fixture(scope='module', params=['a', 'b'])
@saved_fixture
def my_fix2():
    return 1


def test_foo(my_fix):
    assert my_fix == 1


def test_bar(my_fix, my_fix2):
    assert my_fix == 1


def test_synthesis(request, fixture_store):
    # the first is used by the first test: it appears for it and then does not re-appear (not re-created)
    print(list(fixture_store['my_fix'].keys()))
    prefix = get_prefix(request, test_synthesis)
    assert list(fixture_store['my_fix'].keys()) \
           == ['%stest_saved_fixture_module_params.py::test_foo[1]' % prefix,
               '%stest_saved_fixture_module_params.py::test_bar[2-a]' % prefix,
               '%stest_saved_fixture_module_params.py::test_bar[1-b]' % prefix
               ]

    # the second only appears when created
    print(list(fixture_store['my_fix2'].keys()))
    assert list(fixture_store['my_fix2'].keys()) \
           == ['%stest_saved_fixture_module_params.py::test_bar[1-a]' % prefix,
               '%stest_saved_fixture_module_params.py::test_bar[2-b]' % prefix]


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
    module_short_name = test_func.__module__.split('.')[-1]
    module_idx = last_node_id.index(module_short_name)
    prefix = last_node_id[0:module_idx]
    return prefix