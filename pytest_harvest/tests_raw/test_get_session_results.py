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
        expected_keys.update({mark.args[0] for mark in get_pytest_parametrize_marks(test_foo)})
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
    ref_pytest_23 = 'TestX::()::test_easy[True]'
    ref_pytest_45 = ref_pytest_23.replace('()::', '')
    assert list(results_dct.keys())[0] in {ref_pytest_23, ref_pytest_45}

    fmt = 'module'
    results_dct = get_session_synthesis_dct(request.session, filter=TestX.test_easy, test_id_format=fmt)
    # this does not work when we run the test from the meta-tester
    # assert list(results_dct.keys())[0] == 'test_get_session_results.py::TestX::()::test_easy[True]'
    ref_pytest_23_b = "test_get_session_results.py::TestX::()::test_easy[True]"
    pattern_str_pytest_23 = re.escape(ref_pytest_23_b)\
        .replace(re.escape('test_get_session_results'), '^[a-zA-Z0-9_]*?')  # replace the file name with a non-greedy capturer
    ref_pytest_45_b = "test_get_session_results.py::TestX::test_easy[True]"
    pattern_str_pytest_45 = re.escape(ref_pytest_45_b)\
        .replace(re.escape('test_get_session_results'), '^[a-zA-Z0-9_]*?')  # replace the file name with a non-greedy capturer
    assert re.match(pattern_str_pytest_23, list(results_dct.keys())[0]) \
           or re.match(pattern_str_pytest_45, list(results_dct.keys())[0])

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
    fixture_names = get_all_pytest_fixture_names(request.session, filter=test_get_all_pytest_fixture_names.__module__)
    clear_environment_fixture(fixture_names)
    assert fixture_names == ['make_synthesis', 'a_number_str', 'dummy']

    fixture_names = get_all_pytest_fixture_names(request.session, filter=test_foo)
    clear_environment_fixture(fixture_names)
    assert fixture_names == ['make_synthesis', 'a_number_str', 'dummy']


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


def clear_environment_fixture(fixture_names):
    """
    sometimes (at least in Travis), an autouse=True 'environment' session fixture appears.
    This utility function can be used to remove it.
    """
    try:
        fixture_names.remove('environment')
    except ValueError:
        pass


# -------- tools to get the parametrization mark whatever the pytest version
class _LegacyMark:
    __slots__ = "args", "kwargs"

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def get_pytest_parametrize_marks(f):
    """
    Returns the @pytest.mark.parametrize marks associated with a function (and only those)

    :param f:
    :return: a tuple containing all 'parametrize' marks
    """
    # pytest > 3.2.0
    marks = getattr(f, 'pytestmark', None)
    if marks is not None:
        return tuple(m for m in marks if m.name == 'parametrize')
    else:
        # older versions
        mark_info = getattr(f, 'parametrize', None)
        if mark_info is not None:
            # mark_info.args contains a list of (name, values)
            if len(mark_info.args) % 2 != 0:
                raise ValueError("internal pytest compatibility error - please report")
            nb_parameters = len(mark_info.args) // 2
            if nb_parameters > 1 and len(mark_info.kwargs) > 0:
                raise ValueError("Unfortunately with this old pytest version it is not possible to have several "
                                 "parametrization decorators")
            res = []
            for i in range(nb_parameters):
                param_name, param_values = mark_info.args[2*i:2*(i+1)]
                res.append(_LegacyMark(param_name, param_values, **mark_info.kwargs))
            return tuple(res)
        else:
            return ()
