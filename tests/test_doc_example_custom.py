from collections import OrderedDict
from random import random

import pandas as pd
import pytest
from tabulate import tabulate

from pytest_harvest import create_results_bag_fixture, saved_fixture, get_session_synthesis_dct


# ---------- The function to test -------
def my_algorithm(param, data):
    # let's return a random accuracy !
    return random()


# ---------- Tests
# A module-scoped store
@pytest.fixture(scope='module', autouse=True)
def my_store():
    return OrderedDict()


# A module-scoped results bag fixture
my_results_bag = create_results_bag_fixture('my_store', name='my_results_bag')


@pytest.fixture(params=['A', 'B', 'C'])
@saved_fixture('my_store')
def dataset(request):
    """Represents a dataset fixture."""
    return "my dataset #%s" % request.param


@pytest.mark.parametrize("algo_param", [1, 2], ids=str)
def test_my_app_bench(algo_param, dataset, my_results_bag):
    """
    This test applies the algorithm with various parameters (`algo_param`)
    on various datasets (`dataset`).

    Accuracies are stored in a results bag (`my_results_bag`)
    """
    # apply the algorithm with param `algo_param` on dataset `dataset`
    accuracy = my_algorithm(algo_param, dataset)
    # store it in the results bag
    my_results_bag.accuracy = accuracy


def test_basic():
    """Another test, to show how it appears in the results"""
    pass


# Our test synthesis
def test_synthesis(request, my_store):
    """
    An example test that retrieves synthesis information about this module
    """
    # retrieve the synthesis, merged with the fixture store
    results_dct = get_session_synthesis_dct(request.session, filter=test_synthesis.__module__,
                                            durations_in_ms=True, test_id_format='function',
                                            status_details=False, fixture_store=my_store,
                                            flatten=True, flatten_more='my_results_bag')

    # print keys and first node details
    print("\nKeys:\n" + "\n".join(list(results_dct.keys())))
    print("\nFirst node:\n" + "\n".join(repr(k) + ": " + repr(v) for k, v in list(results_dct.values())[0].items()))

    # convert to a pandas dataframe
    results_df = pd.DataFrame.from_dict(results_dct, orient='index')
    results_df = results_df.loc[list(results_dct.keys()), :]          # fix rows order
    results_df.index.name = 'test_id'                                 # set index name
    results_df.drop(['pytest_obj'], axis=1, inplace=True)             # drop pytest object column

    # print using tabulate
    print(tabulate(results_df, headers='keys'))


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
