# META
# {'passed': 4, 'skipped': 1, 'failed': 1}
# END META
import os
from collections import OrderedDict

from itertools import product

import pytest
from pytest_harvest import get_session_synthesis_dct
from pytest_harvest.common import yield_fixture


# init
this_file_name = os.path.split(__file__)[1]

# parametrized fixture
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


# skipped test
def test_skipped():
    pytest.skip("normal, intended skip here")


# failing test
def test_failing():
    pytest.fail("normal, intended failure here")


@yield_fixture(scope='session', autouse=True)
def make_synthesis(request):
    yield

    #  teardown callback
    synth_dct = get_session_synthesis_dct(request.session)

    from pprint import pprint
    pprint(dict(synth_dct))

    # asserts
    these_tests = [item.nodeid for item in request.session.items if this_file_name in item.nodeid]

    # -- first check that synth_dct contains all these test nodes
    missing = set(these_tests) - set(synth_dct.keys())
    assert len(missing) == 0

    # compute the parameter values for all tests in order
    params = list(product(fixture_params, test_params))

    # -- check that all test foo nodes appear as success and contain the right information
    test_foo_nodes = [nid for nid in these_tests if test_foo.__name__ in nid]
    for i, nodeid in enumerate(test_foo_nodes):
        node_synth_dct = synth_dct[nodeid]
        assert set(node_synth_dct.keys()) == {'pytest_obj',
                                              'pytest_status',
                                              'pytest_duration',
                                              'pytest_status_details',
                                              'pytest_params'
                                              }
        # main test information
        assert node_synth_dct['pytest_obj'] == test_foo
        assert node_synth_dct['pytest_status'] == 'passed'
        assert node_synth_dct['pytest_duration'] >= 0

        # test status details
        stages = ['setup', 'call', 'teardown']
        assert set(node_synth_dct['pytest_status_details'].keys()) == set(stages)
        for step in stages:
            assert len(node_synth_dct['pytest_status_details'][step]) == 2
            assert node_synth_dct['pytest_status_details'][step][0] == 'passed'
            assert node_synth_dct['pytest_status_details'][step][1] >= 0

        # parameter values
        assert set(node_synth_dct['pytest_params'].keys()) == {'p', 'a_number_str'}
        assert node_synth_dct['pytest_params']['a_number_str'] == params[i][0]
        assert node_synth_dct['pytest_params']['p'] == params[i][1]
