import sys
from collections import OrderedDict
from itertools import chain
from warnings import warn

try: # python 3.5+
    from typing import Union, Iterable, Mapping, Any
except ImportError:
    pass

from pytest_harvest.common import HARVEST_PREFIX


PYTEST_OBJ_NAME = 'pytest_obj'


def get_session_synthesis_dct(session_or_request,
                              test_id_format='full',   #
                              status_details=False,    # type: bool
                              durations_in_ms=False,   # type: bool
                              pytest_prefix=None,      # type: bool
                              filter=None,             # type: Any
                              filter_incomplete=True,  # type: bool
                              flatten=False,           # type: bool
                              fixture_store=None,      # type: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]
                              flatten_more=None        # type: Union[str, Iterable[str], Mapping[str, str]]
                              ):
    """
    Returns a dictionary containing a synthesis of what is available currently in the `pytest` session object provided.

    For each entry, the key is the test id, and the value is a dictionary containing:
     - 'pytest_obj': the object under test, typically a test function
     - 'pytest_status': the overall status ('failing', 'skipped', 'passed')
     - 'pytest_duration': the duration of the 'call' step. By default this is the pytest unit (s) but if you set
     `durations_in_ms=True` it becomes (ms)
     - 'pytest_status_details': a dictionary containing step-by-step status details for all pytest steps ('setup',
     'call', 'teardown'). This is only included if `status_details=True` (not by default)

    It is possible to process the test id (the keys) using the `test_id_format` option. Let's assume that the id is
    `pytest_steps/tests_raw/test_wrapped_in_class.py::TestX::()::test_easy[p1-p2]`. Here are the returned test ids
    depending on the selected `test_id_format`
     - 'function' will return `test_easy[p1-p2]`
     - 'class' will return `TestX::()::test_easy[p1-p2]`
     - 'module' will return `test_wrapped_in_class.py::TestX::()::test_easy[...]`
     - 'full' will return the original id (this is the default behaviour)
    In addition one can provide a custom string handling function that will be called for each test id to process.

    The 'pytest' prefix in front of all these items (except `pytest_obj`) is by default added in non-flatten mode and
    removed in flatten mode. To force one of these you can set `pytest_prefix` to True or False.

    An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test
    functions) and/or module names.

    If this method is called before the end of the pytest session, some nodes might be incomplete, i.e. they will not
    have data for the three stages (setup/call/teardown). By default these nodes are filtered out but you can set
    `filter_incomplete=False` to make them appear. They will have a special 'pending' synthesis status.

    An optional collection of storage objects can be provided, so as to merge them into the resulting dictionary.

    Finally a `flatten_output` option allows users to get a flat dictionary output instead of nested status details,
    parameters dict, and storage dicts.

    :param session: a pytest session object.
    :param test_id_format: one of 'function', 'class', 'module', or 'full' (default), or a custom test id processing
        function.
    :param status_details: a flag indicating if pytest status details per stage (setup/call/teardown) should be
        included. Default=`False`: only the pytest status summary is provided.
    :param durations_in_ms: by default `pytest` measures durations in seconds so they are outputed in this unit. You
        can turn the flag to True to output milliseconds instead.
    :param pytest_prefix: to add (True) or remove (False) the 'pytest_' prefix in front of status, duration and status
        details. Typically useful in flatten mode when the names are not ambiguous. By default it is None, which
        means =(not flatten)
    :param filter: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned
        items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use
        module names.
    :param filter_incomplete: a boolean indicating if incomplete nodes (without the three stages setup/call/teardown)
        should appear in the results (False) or not (True, default).
    :param flatten: a boolean (default `False`) indicating if the resulting dictionary should be flattened. If it
        set to `True`, the 3 nested dictionaries (pytest status details, parameters, and optionally storages)
        will have their contents directly copied in the first level (with a prefix added in case of pytest status
        details).
    :param fixture_store: a singleton or iterable containing dict-like fixture storage objects (see
        `@saved_fixture` and `create_results_bag`). If flatten=`False` the contents of these dictionaries will be added
        to the output in a dedicated 'fixtures' entry. If flatten=True all of their contents will be included directly.
    :param flatten_more: a singleton, iterable or dictionary containing fixture names to flatten one level more in case
        flatten=True. If a dictionary is provided, the key should be the fixture name, and the value should be a prefix
        used for flattening its contents
    :return: a dictionary where the keys are pytest node ids. Each value is also a dictionary, containing information
        available from pytest concerning the test node, and optionally storage contents if `storage_dcts` is provided.
    """
    res_dct = OrderedDict()

    # extract session if needed
    if hasattr(session_or_request, 'session') and session_or_request.session is not session_or_request:
        request = session_or_request
        session = request.session
    else:
        request = None
        session = session_or_request

    # Optional test id formatter
    if test_id_format == 'function':
        def test_id_format(test_id):
            return test_id.split('::')[-1]
    elif test_id_format == 'class':
        def test_id_format(test_id):
            return '::'.join(test_id.split('::')[1:])
    elif test_id_format == 'module':
        def test_id_format(test_id):
            return test_id.replace('\\', '/').split('/')[-1]
    elif test_id_format == 'full':
        def test_id_format(test_id):
            return test_id
    elif callable(test_id_format):
        pass  # use it directly
    else:
        raise ValueError("`test_id_format` should be one of {'function', 'class', 'module', 'full'} or be a custom "
                         "function. Found '%s'" % test_id_format)

    # Optional 'pytest_' prefix in front of status and duration
    if pytest_prefix is None:
        pytest_prefix = not flatten
    if pytest_prefix:
        pytest_prefix = 'pytest_'
    else:
        pytest_prefix = ''

    # Optional filter
    filtered_items = filter_session_items(session, filter)

    # fixture store check
    if fixture_store is not None:
        try:
            fixture_store_items = fixture_store.items()
        except AttributeError:
            # not a dict: an iterable of dict
            fixture_store_items = list(chain(store.items() for store in fixture_store))

    # flatten_more check
    if flatten_more is not None:
        if isinstance(flatten_more, dict):
            flatten_more_prefixes_dct = flatten_more.items()
        elif isinstance(flatten_more, str):
            # single name ?
            flatten_more_prefixes_dct = {flatten_more: ''}
        else:
            # iterable ?
            flatten_more_prefixes_dct = {k: '' for k in flatten_more}

    # For each item add an entry
    for item in filtered_items:
        item_dct = OrderedDict()

        # Fill the dictionary with information about this test node
        # -- test object
        item_dct[PYTEST_OBJ_NAME] = item.obj

        # -- test status: this information is available thanks to our hook in plugin.py
        (test_status, test_duration), status_dct = get_pytest_status(item, durations_in_ms=durations_in_ms,
                                                                     current_request=request)

        if test_status not in {'pending', 'unknown'} or not filter_incomplete:
            # -- parameters (of tests and fixtures)
            param_dct = get_pytest_params(item)

            # Fill according to mode
            item_dct[pytest_prefix + "status"] = test_status
            item_dct[pytest_prefix + "duration_" + ('ms' if durations_in_ms else 's')] = test_duration
            if flatten:
                if status_details:
                    for k, v in status_dct.items():
                        item_dct[pytest_prefix + "status__" + k] = v
                item_dct.update(param_dct)
            else:
                if status_details:
                    item_dct[pytest_prefix + "status_details"] = status_dct
                item_dct[pytest_prefix + "params"] = param_dct

            # -- fixture storages
            # For info: https://docs.pytest.org/en/latest/_modules/_pytest/runner.html
            # used_fixtures = sorted(item._fixtureinfo.name2fixturedefs.keys())
            # if used_fixtures:
            #     tw.write(" (fixtures used: {})".format(", ".join(used_fixtures)))
            if fixture_store is not None:
                if not flatten:
                    item_dct['fixtures'] = OrderedDict()

                for fixture_name, fixture_dct in fixture_store_items:

                    # if this fixture is available for this test
                    if item.nodeid in fixture_dct:
                        # get the fixture value for this test
                        fix_val = fixture_dct[item.nodeid]

                        # store it in the appropriate format
                        if flatten:
                            if flatten_more is not None and fixture_name in flatten_more_prefixes_dct:
                                prefix = flatten_more_prefixes_dct[fixture_name]
                                # flatten more
                                for k, v in fix_val.items():
                                    item_dct[prefix + k] = v
                            else:
                                item_dct[fixture_name] = fix_val
                        else:
                            item_dct['fixtures'][fixture_name] = fix_val

            # Finally store in the main dictionary
            res_dct[test_id_format(item.nodeid)] = item_dct

    return res_dct


def filter_session_items(session,
                         filter=None,  # type: Any
                         ):
    """
    Filters pytest session item in the provided `session`
    An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test
    functions) and/or module names.

    :param session:
    :param filter: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned
        items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use
        module names.
    :return:
    """
    if filter is not None:
        filterset = _get_filterset(filter)
        filtered_items = (item for item in session.items if _pytest_item_matches_filter(item, filterset))
    else:
        filtered_items = session.items
    return filtered_items


def get_all_pytest_param_names(session,
                               filter=None,              # type: Any
                               filter_incomplete=False,  # type: bool
                               ):
    """
    Returns the list of all unique parameter names used in all items in the provided session, with given filter.

    An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test
    functions) and/or module names.

    If this method is called before the end of the pytest session, some nodes might be incomplete, i.e. they will not
    have data for the three stages (setup/call/teardown). By default these nodes are filtered out but you can set
    `filter_incomplete=False` to make them appear. They will have a special 'pending' synthesis status.

    :param session: a pytest session object.
    :param filter: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned
        items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use
        modules or the special `THIS MODULE` item.
    :param filter_incomplete: a boolean indicating if incomplete nodes (without the three stages setup/call/teardown)
        should appear in the results (False) or not (True). Note: by default incomplete nodes DO APPEAR (this is
        different from get_session_synthesis_dct behaviour)
    :return:
    """
    dset = set()

    # relies on the fact that dset.add() always returns None
    # thanks https://stackoverflow.com/questions/6197409/ordered-sets-python-2-7
    return [k for item in filter_session_items(session, filter=filter)
            for k in get_pytest_params(item)
            if k not in dset and not (filter_incomplete and is_pytest_incomplete(item))
               and not dset.add(k)]


def get_all_pytest_fixture_names(session,
                                 filter=None,              # type: Any
                                 filter_incomplete=False,  # type: bool
                                 ):
    """
    Returns the list of all unique fixture names used in all items in the provided session, with given filter.

    An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test
    functions) and/or module names.

    If this method is called before the end of the pytest session, some nodes might be incomplete, i.e. they will not
    have data for the three stages (setup/call/teardown). By default these nodes are filtered out but you can set
    `filter_incomplete=False` to make them appear. They will have a special 'pending' synthesis status.

    :param session: a pytest session object.
    :param filter: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned
        items will only by pytest nodes for which the pytest object is one of the ones provided). One can also use
        modules or the special `THIS MODULE` item.
    :param filter_incomplete: a boolean indicating if incomplete nodes (without the three stages setup/call/teardown)
        should appear in the results (False) or not (True). Note: by default incomplete nodes DO APPEAR (this is
        different from get_session_synthesis_dct behaviour)
    :return:
    """
    dset = set()

    # relies on the fact that dset.add() always returns None
    # thanks https://stackoverflow.com/questions/6197409/ordered-sets-python-2-7
    return [k for item in filter_session_items(session, filter=filter)
            for k in get_pytest_fixture_names(item)
            if k not in dset and not (filter_incomplete and is_pytest_incomplete(item))
               and not dset.add(k)]


# ------------ item-related -------------
def pytest_item_matches_filter(item, filter):
    """
    Returns True if pytest session item `item` matches filter `filter`

    :param item: an item inside a pytest session
    :param filter:
    :return:
    """
    filterset = _get_filterset(filter)
    return _pytest_item_matches_filter(item, filterset)


def _pytest_item_matches_filter(item, filterset):
    """Internal method used to check if item matches filter set"""
    item_obj = item.obj
    if item_obj in filterset:
        return True
    # support class methods: the item object can be a bound method while the filter is maybe not
    elif _is_unbound_present(item_obj, filterset):
        return True
    elif any(item_obj.__module__ == f for f in filterset):
        return True
    else:
        return False


def _is_unbound_present(item_obj, filterset):
    """
    Returns True if item_obj is a bound method and that its unbound version is in filterset
    :param item_obj:
    :param filterset:
    :return:
    """
    if sys.version_info >= (3,):
        # Python 3
        not_bound_fct = getattr(item_obj, '__func__', None)
        if not_bound_fct is None:
            return False
        else:
            return not_bound_fct in filterset
    else:
        # Python 2 has the concept of "unbound method" and behaves a bit diferently
        # see https://stackoverflow.com/questions/14574641/python-get-unbound-class-method
        not_bound_fct = getattr(item_obj, 'im_func', None)
        if not_bound_fct is None:
            return False
        elif not_bound_fct in filterset:
            return True
        else:
            # maybe the filterset contains a "truly unbound" method ?
            return not_bound_fct in {getattr(f, 'im_func', None) for f in filterset}


def _get_pytest_status_keys(item):
    return [k for k in vars(item) if k.startswith(HARVEST_PREFIX)]


def is_pytest_incomplete(item):
    return len(_get_pytest_status_keys(item)) < 3


def get_pytest_status(item, durations_in_ms=False, current_request=None):
    """
    Returns a dictionary containing item's pytest status (success/skipped/failed, duration converted to ms) for
    each pytest phase, and a tuple synthesizing the information.

    The synthesis status contains the worst status of all phases (setup/call/teardown), or 'pending' if there are less
    than 3 phases.

    The synthesis duration is equal to the duration of the 'call' phase (not to the sum of all phases: indeed, we are
    mostly interested in the test call itself).

    :param item: a pytest session.item
    :param durations_in_ms: by default `pytest` measures durations in seconds so they are outputed in this unit. You
        can turn the flag to True to output milliseconds instead.
    :param current_request: if a non-None `request` is provided and the item is precisely the one from the request,
        then the status will be 'pending'
    :return: a tuple ((test_status, test_duration), status_dct)
    """

    # the status keys that have been stored by our plugin.py module
    status_keys = _get_pytest_status_keys(item)
    if len(status_keys) == 0:
        if current_request is not None and current_request.node == item:
            # do not raise a warning: it is normal that there is no information, the node is being called.
            test_status = 'pending'
        else:
            # warn("[pytest-harvest] Test items status is not available. You should maybe install pytest-harvest with "
            #      "pip. If it is already the case, you case try to force-use it by adding "
            #      "`pytest_plugins = ['harvest']` to your conftest.py. But for normal use this should not be required,"
            #      "installing with pip should be enough.")
            test_status = 'unknown'

        test_duration = None
        status_dct = dict()
    else:
        # adjust duration factor according to target unit
        duration_factor = (1000 if durations_in_ms else 1)

        # create the status dictionary for that item
        status_dct = OrderedDict()
        test_status = 'passed'
        test_duration = None
        for k in status_keys:
            statusreport = getattr(item, k)
            status_dct[statusreport.when] = (statusreport.outcome, statusreport.duration * duration_factor)
            # update global test status
            if test_status == 'passed' \
                    or (test_status == 'skipped' and statusreport.outcome != 'passed'):
                test_status = statusreport.outcome
            # global test duration is the duration of the "call" step only
            if statusreport.when == "call":
                test_duration = statusreport.duration * duration_factor

        if len(status_keys) < 3:
            # this is an incomplete test
            test_status = 'pending'

    return (test_status, test_duration), status_dct


def get_pytest_param_names(item):
    """ Returns a list containing a pytest session item's parameter """
    return list(get_pytest_params(item).keys())


def get_pytest_params(item):
    """ Returns a dictionary containing a pytest session item's parameters """

    param_dct = OrderedDict()
    for param_name in item.fixturenames:  # note: item.funcargnames gives the exact same list
        if hasattr(item, 'callspec'):
            if param_name in item.callspec.params:
                if item.session._fixturemanager.getfixturedefs(param_name, item.nodeid) is not None:
                    # Fixture parameters have the same name than the fixtures themselves! change it
                    param_dct[param_name + '_param'] = item.callspec.params[param_name]
                else:
                    # Non-fixture parameter: ok
                    param_dct[param_name] = item.callspec.params[param_name]
            else:
                # this is a non-parametrized fixture: it is not available by default in item, this is normal pytest
                # behaviour (hence the @saved_fixture decorator)
                pass

    return param_dct


def get_pytest_fixture_names(item):
    """ Returns a list containing a pytest session item's fixture names """

    fixture_names = []
    for param_name in item.fixturenames:  # note: item.funcargnames gives the exact same list
        if hasattr(item, 'callspec'):
            if param_name in item.callspec.params:
                if item.session._fixturemanager.getfixturedefs(param_name, item.nodeid) is not None:
                    fixture_names.append(param_name)

    return fixture_names


# --- misc
def _get_filterset(filter):
    """
    Always returns a set, even if the filter is a string (module name) or single object
    :param filter:
    :return:
    """
    if isinstance(filter, str):
        filter = {filter}
    else:
        try:
            iter(filter)
            filter = set(filter)
        except TypeError:
            # TypeError: '<....>' object is not iterable
            filter = {filter}
    return filter
