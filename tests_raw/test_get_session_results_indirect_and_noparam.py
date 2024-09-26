# META
# {'passed': 5, 'skipped': 0, 'failed': 0}
# END META
import pytest
from pytest_harvest import get_all_pytest_fixture_names


# -------- indirect parametrized fixture
fixture_params = [1, 2]


@pytest.fixture(params=fixture_params)
def a_number_str_p(request):
    return request.param


@pytest.fixture
def a_number_str(a_number_str_p):
    """ This fixture is indirectly parametrized  by its dependency """
    return "my_fix #%s" % a_number_str_p


def test_foo(a_number_str):
    pass


def test_get_all_pytest_fixture_names_indirect(request):
    """Tests that get_all_pytest_fixture_names works"""
    fixture_names = get_all_pytest_fixture_names(request.session, filter=test_foo)
    clear_environment_fixture(fixture_names)
    assert fixture_names == ['a_number_str', 'a_number_str_p']


# ------------ not parametrized fixture
@pytest.fixture
def dummy():
    """ This fixture has no parameter """
    return "hello!"


def test_foo2(dummy):
    pass


def test_get_all_pytest_fixture_names_no_param(request):
    """Tests that get_all_pytest_fixture_names works"""
    fixture_names = get_all_pytest_fixture_names(request.session, filter=test_foo2)
    clear_environment_fixture(fixture_names)
    assert fixture_names == ['dummy']


def clear_environment_fixture(fixture_names):
    """
    sometimes (at least in Travis), an autouse=True 'environment' session fixture appears.
    This utility function can be used to remove it.
    """
    try:
        fixture_names.remove('environment')
    except ValueError:
        pass
