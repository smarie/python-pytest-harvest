# META
# {'passed': 2}
# END META

from collections import OrderedDict

import pytest

from pytest_harvest import saved_fixture


STORE = OrderedDict()


@saved_fixture(STORE)
@pytest.fixture(params=[1, 2])
def my_fix(request):
    return request.param


def test_basic_fixture_cache(my_fix):
    """"""
    print(my_fix)


# -----------------------------------------


def final_test(request):
    """This is the "test" that will be called """
    assert 'my_fix' in STORE
    assert list(STORE['my_fix'].keys()) == [item.nodeid for item in request.session.items]
    assert list(STORE['my_fix'].values()) == [1, 2]


@pytest.fixture(scope='session', autouse=True)
def collect_all(request):
    # This is a way, compliant with legacy pytest 2.8, to register a teardown callback
    request.addfinalizer(lambda: final_test(request))
