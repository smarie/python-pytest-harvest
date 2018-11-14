# META
# {'passed': 8, 'skipped': 0, 'failed': 0}
# END META
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
def store():
    return OrderedDict()


# A module-scoped results bag fixture
my_results = create_results_bag_fixture('store', name='my_results')


@pytest.fixture(params=['A', 'B', 'C'])
@saved_fixture('store')
def dataset(request):
    """Represents a dataset fixture."""
    return "my dataset #%s" % request.param


@pytest.mark.parametrize("algo_param", [1, 2], ids=str)
def test_my_app_bench(algo_param, dataset, my_results):
    """
    This test applies the algorithm with various parameters (`algo_param`)
    on various datasets (`dataset`).

    Accuracies are stored in a results bag (`results_bag`)
    """
    # apply the algorithm with param `algo_param` on dataset `dataset`
    accuracy = my_algorithm(algo_param, dataset)
    # store it in the results bag
    my_results.accuracy = accuracy


def test_basic():
    """Another test, to show how it appears in the results"""
    pass


# Our test synthesis
def test_synthesis(request, store):
    """
    An example test that retrieves synthesis information about this module
    """
    # retrieve the synthesis, merged with the fixture store
    results_dct = get_session_synthesis_dct(request.session, filter=test_synthesis.__module__,
                                            durations_in_ms=True,
                                            status_details=False, fixture_store=store,
                                            flatten=True, flatten_more='my_results')

    # print keys and first node details
    print("\nKeys:\n" + "\n".join(list(results_dct.keys())))
    print("\nFirst node:\n" + "\n".join(repr(k) + ": " + repr(v) for k, v in list(results_dct.values())[0].items()))

    # convert to a pandas dataframe
    results_df = pd.DataFrame.from_dict(results_dct, orient='index')
    results_df.index = results_df.index.to_series().apply(lambda test_id: test_id.split('::')[-1])  # remove full path
    results_df.drop(['pytest_obj'], axis=1, inplace=True)                                  # drop pytest object column

    # print using tabulate
    print(tabulate(results_df, headers='keys'))
