# META
# {'passed': 8, 'skipped': 0, 'failed': 0}
# END META
import pytest


# parametrized fixture
from pytest_harvest import HARVEST_PREFIX

fixture_params = [1, 2]


@pytest.fixture(params=fixture_params)
def a_number_str(request):
    return "my_fix #%s" % request.param


# unparametrized fixture
@pytest.fixture
def dummy():
    return "hey there !"


# parametrized test
test_params = ['hello', 'world']


@pytest.mark.parametrize('p', test_params, ids=str)
def test_foo(p, a_number_str, dummy):
    print(p + a_number_str)


def test_synthesis_default_module_dct(module_results_dct):
    """
    Tests that that `module_results_dct` fixture is present and contains the correct contents.
    """
    assert set(module_results_dct.keys()) == {'test_foo[{i}-{p}]'.format(i=i, p=p)
                                              for i in fixture_params for p in test_params}


def test_synthesis_default_module_df(module_results_df):
    """
    Tests that that `module_results_dct` fixture is present and contains the correct contents.
    """
    assert module_results_df.index.name == 'test_id'
    assert list(module_results_df.index.values) == ['test_foo[{i}-{p}]'.format(i=i, p=p)
                                                    for i in fixture_params for p in test_params] \
                                                    + ['test_synthesis_default_module_dct']


def test_synthesis_default_session_dct(request, session_results_dct):
    """
    Tests that the `session_results_dct` fixture is present and contains the correct contents.
    """
    # assert that there are as many entries as completed items (items that already have a 'harvst' report built)
    assert len(session_results_dct) == len([i for i in request.session.items if hasattr(i, HARVEST_PREFIX + 'call')])


def test_synthesis_default_session_df(request, session_results_df):
    """
    Tests that the `session_results_dct` fixture is present and contains the correct contents.
    """
    # assert that there are as many entries as completed items (items that already have a 'harvst' report built)
    assert len(session_results_df) == len([i for i in request.session.items if hasattr(i, HARVEST_PREFIX + 'call')])
