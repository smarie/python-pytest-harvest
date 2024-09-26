from random import random

import pytest
from tabulate import tabulate

from pytest_harvest import saved_fixture


# ---------- The function to test -------
def my_algorithm(param, data):
    # let's return a random accuracy !
    return random()


# ---------- Tests
@pytest.fixture(params=['A', 'B', 'C'])
@saved_fixture
def dataset(request):
    """Represents a dataset fixture."""
    return "my dataset #%s" % request.param


@pytest.mark.parametrize("algo_param", [1, 2], ids=str)
def test_my_app_bench(algo_param, dataset, results_bag):
    """
    This test applies the algorithm with various parameters (`algo_param`)
    on various datasets (`dataset`).

    Accuracies are stored in a results bag (`results_bag`)
    """
    # apply the algorithm with param `algo_param` on dataset `dataset`
    accuracy = my_algorithm(algo_param, dataset)
    # store it in the results bag
    results_bag.accuracy = accuracy


def test_basic():
    """Another test, to show how it appears in the results"""
    pass


# Our test synthesis
def test_synthesis(module_results_df):
    """
    An example test that retrieves synthesis information about this module
    """
    # print using tabulate
    print(tabulate(module_results_df, headers='keys'))


# ------- Output -------
#
# test_id                 status      duration_ms    algo_param  dataset           accuracy
# ----------------------  --------  -------------  ------------  -------------  -----------
# test_basic              passed         0.999928           nan  nan            nan
# test_my_app_bench[A-1]  passed         0                    1  my dataset #A    0.818458
# test_my_app_bench[A-2]  passed         0                    2  my dataset #A    0.0364919
# test_my_app_bench[B-1]  passed         0                    1  my dataset #B    0.0885096
# test_my_app_bench[B-2]  passed         1.0004               2  my dataset #B    0.826001
# test_my_app_bench[C-1]  passed         0                    1  my dataset #C    0.700515
# test_my_app_bench[C-2]  passed         0                    2  my dataset #C    0.281405
#
