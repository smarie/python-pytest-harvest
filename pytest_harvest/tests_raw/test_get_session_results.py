# META
# {'passed': 9, 'skipped': 1, 'failed': 1}
# END META
import os
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


@pytest.mark.parametrize('flatten', [False, True], ids="flatten={}".format)
def test_foo_synthesis_all_options(request, flatten):
    """
    Tests that the synthesis is ok

    :param request:
    :return:
    """
    # Get the synthesis dictionary concerning `test_foo`
    synth_dct = get_session_synthesis_dct(request.session, flatten=flatten, filter=test_foo)

    # from pprint import pprint
    # pprint(dict(synth_dct))

    # Check the returned dictionary contents
    expected_keys = {'pytest_obj',
                     'pytest_status',
                     'pytest_duration'}
    stages = ['setup', 'call', 'teardown']
    if not flatten:
        expected_keys.update({'pytest_status_details', 'pytest_params'})
    else:
        expected_keys.update({('pytest_status__' + stage) for stage in stages})
        # add parameters
        expected_keys.update({mark.args[0] for mark in test_foo.parametrize})
        # add parametrized fixtures
        expected_keys.update({parametrized_fixture.__name__ for parametrized_fixture in [a_number_str]})

    # compute the parameter values for all tests in order
    params = list(product(fixture_params, test_params))

    for i, (nodeid, nodeinfo) in enumerate(synth_dct.items()):

        # check that all keys are present
        assert set(nodeinfo.keys()) == expected_keys

        # main test information
        assert nodeinfo['pytest_obj'] == test_foo  # check that the filter worked
        assert nodeinfo['pytest_status'] == 'passed'
        assert nodeinfo['pytest_duration'] >= 0

        # test status details
        if not flatten:
            assert set(nodeinfo['pytest_status_details'].keys()) == set(stages)
        for step in stages:
            if flatten:
                step_info = nodeinfo['pytest_status__' + step]
            else:
                step_info = nodeinfo['pytest_status_details'][step]
            assert len(step_info) == 2
            assert step_info[0] == 'passed'
            assert step_info[1] >= 0

        # parameter values
        if flatten:
            param_dct = nodeinfo
        else:
            assert set(nodeinfo['pytest_params'].keys()) == {'p', 'a_number_str'}
            param_dct = nodeinfo['pytest_params']

        assert param_dct['a_number_str'] == params[i][0]
        assert param_dct['p'] == params[i][1]


# skipped test
def test_skipped():
    pytest.skip("normal, intended skip here")


# failing test
def test_failing():
    pytest.fail("normal, intended failure here")


def test_synthesis_skipped(request):
    """ Tests that the synthesis concerning the skipped test is correct """
    synth_dct = get_session_synthesis_dct(request.session, filter=[test_skipped])
    for test_id, v in synth_dct.items():
        assert v['pytest_status'] == 'skipped'


def test_synthesis_failed(request):
    """ Tests that the synthesis concerning the failed test is correct """
    synth_dct = get_session_synthesis_dct(request.session, filter=[test_failing])
    for test_id, v in synth_dct.items():
        assert v['pytest_status'] == 'failed'


def test_synthesis_contains_everything(request):
    """ Tests that the synthesis contains all test nodes """
    # retrieve session results
    synth_dct = get_session_synthesis_dct(request.session)

    # asserts
    these_tests = [item.nodeid for item in request.session.items if this_file_name in item.nodeid]

    # check that synth_dct contains all these test nodes
    missing = set(these_tests) - set(synth_dct.keys())
    assert len(missing) == 0


@yield_fixture(scope='session', autouse=True)
def make_synthesis(request):
    """This checks that the session-scoped fixture teardown hook works as well"""
    yield
    test_synthesis_contains_everything(request)
