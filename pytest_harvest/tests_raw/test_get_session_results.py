# META
# {'passed': 16, 'skipped': 1, 'failed': 1}
# END META
import os
from itertools import product
import re

import pytest
from pytest_harvest import get_session_synthesis_dct, get_all_pytest_param_names, get_all_pytest_fixture_names
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
@pytest.mark.parametrize('durations_in_ms', [False, True], ids="duration_in_ms={}".format)
def test_foo_synthesis_all_options(request, flatten, durations_in_ms):
    """
    Tests that the synthesis is ok

    :param request:
    :return:
    """
    # Get the synthesis dictionary concerning `test_foo`
    synth_dct = get_session_synthesis_dct(request.session, status_details=True, flatten=flatten, filter=test_foo,
                                          durations_in_ms=durations_in_ms)

    # from pprint import pprint
    # pprint(dict(synth_dct))

    durations_unit = ('ms' if durations_in_ms else 's')

    # Check the returned dictionary contents
    prefix = '' if flatten else 'pytest_'
    expected_keys = {'pytest_obj',
                     prefix + 'status',
                     prefix + 'duration_' + durations_unit}
    stages = ['setup', 'call', 'teardown']
    if not flatten:
        expected_keys.update({prefix + 'status_details', prefix + 'params'})
    else:
        expected_keys.update({(prefix + 'status__' + stage) for stage in stages})
        # add parameters
        expected_keys.update({mark.args[0] for mark in test_foo.parametrize})
        # add parametrized fixtures
        expected_keys.update({parametrized_fixture.__name__ + '_param' for parametrized_fixture in [a_number_str]})

    # compute the parameter values for all tests in order
    params = list(product(fixture_params, test_params))

    for i, (nodeid, nodeinfo) in enumerate(synth_dct.items()):

        # check that all keys are present
        assert set(nodeinfo.keys()) == expected_keys

        # main test information
        assert nodeinfo['pytest_obj'] == test_foo  # check that the filter worked
        assert nodeinfo[prefix + 'status'] == 'passed'
        assert nodeinfo[prefix + 'duration_' + durations_unit] >= 0

        # test status details
        if not flatten:
            assert set(nodeinfo[prefix + 'status_details'].keys()) == set(stages)
        for step in stages:
            if flatten:
                step_info = nodeinfo[prefix + 'status__' + step]
            else:
                step_info = nodeinfo[prefix + 'status_details'][step]
            assert len(step_info) == 2
            assert step_info[0] == 'passed'
            assert step_info[1] >= 0

        # parameter values
        if flatten:
            param_dct = nodeinfo
        else:
            assert set(nodeinfo[prefix + 'params'].keys()) == {'p', 'a_number_str_param'}
            param_dct = nodeinfo[prefix + 'params']

        assert param_dct['a_number_str_param'] == params[i][0]
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


class TestX:
    @pytest.mark.parametrize('p', [True, False])
    def test_easy(self, p):
        print(2)


def test_synthesis_id_formatting(request):
    """
    Note: we could do this at many other places (hook, teardown of a session-scope fixture...)

    Note2: we could provide helper methods in pytest_harvest to perform the code below more easily
    :param request:
    :param store:
    :return:
    """
    # Get session synthesis filtered on the test function of interest
    # -- to debug the filter:
    # assert pytest_item_matches_filter(request.session.items[28], filter={TestX.test_easy})
    fmt = 'function'
    results_dct = get_session_synthesis_dct(request.session, filter=TestX.test_easy, test_id_format=fmt)
    assert list(results_dct.keys())[0] == 'test_easy[True]'

    fmt = 'class'
    results_dct = get_session_synthesis_dct(request.session, filter=TestX.test_easy, test_id_format=fmt)
    assert list(results_dct.keys())[0] == 'TestX::()::test_easy[True]'

    fmt = 'module'
    results_dct = get_session_synthesis_dct(request.session, filter=TestX.test_easy, test_id_format=fmt)
    # this does not work when we run the test from the meta-tester
    # assert list(results_dct.keys())[0] == 'test_get_session_results.py::TestX::()::test_easy[True]'
    pattern_str = re.escape("test_get_session_results.py::TestX::()::test_easy[True]") \
                            .replace(re.escape('test_get_session_results'), '^[a-zA-Z0-9_]*?')  # replace the file name with a non-greedy capturer
    assert re.match(pattern_str, list(results_dct.keys())[0])

    def fmt(test_id):
        return test_id.split('::')[-1].lower()
    results_dct = get_session_synthesis_dct(request.session, filter=TestX.test_easy, test_id_format=fmt)
    assert list(results_dct.keys())[0] == 'test_easy[true]'


def test_get_all_pytest_param_names(request):
    """Tests that get_all_pytest_param_names works"""
    param_names = get_all_pytest_param_names(request.session, filter=test_get_all_pytest_param_names.__module__)
    assert param_names == ['p', 'a_number_str_param', 'flatten', 'durations_in_ms']

    param_names = get_all_pytest_param_names(request.session, filter=test_foo)
    assert param_names == ['p', 'a_number_str_param']

def test_get_all_pytest_fixture_names(request):
    """Tests that get_all_pytest_fixture_names works"""
    fixture_names = get_all_pytest_fixture_names(request.session, filter=test_get_all_pytest_param_names.__module__)
    assert fixture_names == ['a_number_str']

    fixture_names = get_all_pytest_fixture_names(request.session, filter=test_foo)
    assert fixture_names == ['a_number_str']


def test_synthesis_contains_everything(request):
    """ Tests that the synthesis contains all test nodes """
    # retrieve session results
    synth_dct = get_session_synthesis_dct(request, filter_incomplete=False)

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
