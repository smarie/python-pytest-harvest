from datetime import datetime
import time

import pytest
from tabulate import tabulate

from pytest_harvest import saved_fixture, get_session_synthesis_dct


@pytest.fixture(params=range(2))
@saved_fixture
def person(request):
    """
    A dummy fixture, parametrized so that it has two instances
    """
    if request.param == 0:
        return "world"
    elif request.param == 1:
        return "self"


@pytest.mark.parametrize('double_sleep_time', [False, True], ids=str)
def test_foo(double_sleep_time, person, results_bag):
    """
    A dummy test, parametrized so that it is executed twice.
    """
    print('\n   hello, ' + person + ' !')
    time.sleep(len(person) / 10 * (2 if double_sleep_time else 1))

    # Let's store some things in the results bag
    results_bag.nb_letters = len(person)
    results_bag.current_time = datetime.now().isoformat()


def test_synthesis(module_results_df):
    """
    In this test we just look at the synthesis of all tests
    executed before it, in that module.
    """
    # print the synthesis dataframe
    print("\n   `module_results_df` dataframe:\n")
    # we use 'tabulate' for a nicer format
    print(tabulate(module_results_df, headers='keys', tablefmt="pipe"))

    assert set(module_results_df.columns) == {'pytest_obj',
                                              'status', 'duration_ms',              # pytest info
                                              'double_sleep_time', 'person_param',  # parameters
                                              'person',                             # fixtures
                                              'nb_letters', 'current_time'}         # results
