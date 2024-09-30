# META
# {'passed': 2, 'skipped': 0, 'failed': 0}
# END META

import pytest
from pytest_harvest import saved_fixture, filter_session_items


@pytest.fixture
@saved_fixture
def dummy():
    return 1


def test_dummy(dummy):
    pass


def test_synthesis(request, fixture_store):
    print(fixture_store['dummy'])
    prefix = get_prefix(request, test_synthesis)
    assert dict(fixture_store['dummy']) == {'%s::test_dummy' % prefix: 1}


def get_prefix(request, test_func):
    """
    Utility method to return the prefix to use for node ids, that will work whatever the invocation method.

    If this is not used the test might work when executed in "raw" mode, but might fail when executed using the
    "pytester" plugin (from tests/test_all_raw_with_meta_check). Indeed the "pytester" plugin replaces the module
    name by 'test_all_raw_with_meta_check.py'.

    IMPORTANT: the pytester plugin hangs instead of failing on windows, so a bug is hard to debug. The linux
    version does not so a run on the travis CI usually helps.

    :param request:
    :param test_func:
    :return:
    """
    items = filter_session_items(request.session, filter=test_func.__module__)
    last_node_id = items[-1].nodeid
    prefix = last_node_id.split('::')[0]
    return prefix
