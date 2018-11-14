# META
# {'passed': 9, 'skipped': 0, 'failed': 0}
# END META
from collections import OrderedDict
from itertools import product

import pytest

from pytest_harvest import create_results_bag_fixture, saved_fixture, get_session_synthesis_dct


@pytest.fixture(scope='module', autouse=True)
def store():
    return OrderedDict()


my_results = create_results_bag_fixture('store', name='my_results')


# parametrized fixture
fixture_params = ['A', 'B', 'C']


@pytest.fixture(params=fixture_params)
@saved_fixture('store')
def my_fix(request):
    """Our saved fixture, that will be saved in the store fixture"""
    # convert the parameter to a string so that the fixture is different from the parameter
    return "my_fix #%s" % request.param


# parametrized test
test_params = [10, 20]


@pytest.mark.parametrize('p', test_params, ids="p={}".format)
def test_complete(p, my_fix, my_results):
    """This fake test has a parameter, a fixture and stores things in a results bag"""
    my_results.score = p * 10
    my_results.what = 'hello ' + my_fix


@pytest.mark.parametrize('flatten, flatten_more', [(False, None), (True, None), (True, 'my_results')],
                         ids="flatten={}, flatten_more={}".format)
def test_synthesis(flatten, flatten_more, request, store):
    """Tests that the synthesis dictionary combined with with fixture store is ok"""

    # retrieve the synthesis, merged with the fixture store
    results_dct = get_session_synthesis_dct(request.session, filter=test_complete, status_details=False,
                                            fixture_store=store, flatten=flatten, flatten_more=flatten_more)

    # ------ PRINTS ---------

    # --test node ids
    print("\n".join(list(results_dct.keys())))

    # --zoom on first node
    print("\n".join(repr(k) + ": " + repr(v) for k, v in list(results_dct.values())[0].items()))

    if flatten and flatten_more:
        # -- use tabulate to print
        from tabulate import tabulate
        # print(tabulate(dct, headers='keys'))  not possible, it does not yet support that dict keys represent rows

        # -- use pandas to print
        import pandas as pd
        results_df = pd.DataFrame.from_dict(results_dct, orient='index')
        # (a) remove the full test id path
        results_df.index = results_df.index.to_series().apply(lambda test_id: test_id.split('::')[-1])
        # (b) replace pytest object with its name
        results_df['pytest_obj'] = results_df['pytest_obj'].map(lambda f: f.__name__)

        print(tabulate(results_df, headers='keys', tablefmt="pipe").replace(':-', '--').replace('-:', '--'))

    # ------ ASSERTS ---------

    # compute the parameter values for all tests in order
    params = list(product(fixture_params, test_params))
    assert len(results_dct) == len(params)

    for i, (nodeid, node_info) in enumerate(results_dct.items()):
        if flatten:
            where_dct = node_info
            if flatten_more is None:
                where_dct_results = node_info['my_results']
            else:
                where_dct_results = node_info

        else:
            where_dct = node_info['fixtures']
            where_dct_results = node_info['fixtures']['my_results']

        assert where_dct['my_fix'] == 'my_fix #' + params[i][0]
        assert where_dct_results['score'] == params[i][1] * 10
        assert where_dct_results['what'] == 'hello my_fix #' + params[i][0]
