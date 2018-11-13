from collections import OrderedDict
from itertools import chain
from warnings import warn

try: # python 3.5+
    from typing import Union, Iterable, Mapping, Any
except ImportError:
    pass

from pytest_harvest.plugin import HARVEST_PREFIX


PYTEST_OBJ_NAME = 'pytest_obj'


def get_session_synthesis_dct(session,
                              filter=None,  # type: Any
                              flatten=False,  # type: bool
                              fixture_store=None,  # type: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]
                              flatten_more=None  # type: Union[str, Iterable[str], Mapping[str, str]]
                              ):
    """
    Returns a dictionary containing a synthesis of what is available currently in the `pytest` session object provided.
     - 'pytest_obj': the object under test, typically a test function
     - 'pytest_status': the overall status ('failing', 'skipped', 'passed')
     - 'pytest_duration': the duration of the 'call' step (ms ? TODO check with pytest doc)
     - 'pytest_status_details': a dictionary containing step-by-step status details for all pytest steps ('setup',
     'call', 'teardown')

    An optional `filter` can be provided, that can be a singleton or iterable of pytest objects (typically test
    functions).

    An optional collection of storage objects can be provided, so as to merge them into the resulting dictionary.

    Finally a `flatten_output` option allows users to get a flat dictionary output instead of nested status details,
    parameters dict, and storage dicts.

    :param session: a pytest session object.
    :param filter: a singleton or iterable of pytest objects on which to filter the returned dict on (the returned
        items will only by pytest nodes for which the pytest object is one of the ones provided)
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

    # Optional filter
    if filter is not None:
        try:
            iter(filter)
            filter = set(filter)
        except TypeError:
            # TypeError: '<....>' object is not iterable
            filter = {filter}
        filtered_items = (item for item in session.items if item.obj in filter)
    else:
        filtered_items = session.items

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
        (test_status, test_duration), status_dct = get_pytest_status(item)

        # -- parameters (of tests and fixtures)
        param_dct = get_pytest_params(item)

        # Fill according to mode
        item_dct["pytest_status"] = test_status
        item_dct["pytest_duration"] = test_duration
        if flatten:
            for k, v in status_dct.items():
                item_dct["pytest_status__" + k] = v
            item_dct.update(param_dct)
        else:
            item_dct["pytest_status_details"] = status_dct
            item_dct["pytest_params"] = param_dct

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
        res_dct[item.nodeid] = item_dct

    return res_dct


def get_pytest_status(item):
    """ Returns a dictionary containing item's pytest status (success/skipped/failed, duration) """

    # the status keys that have been stored by our plugin.py module
    status_keys = [k for k in vars(item) if k.startswith(HARVEST_PREFIX)]
    if len(status_keys) == 0:
        warn("[pytest-harvest] Test items status is not available. You should maybe install pytest-harvest with "
             "pip. If it is already the case, you case try to force-use it by adding "
             "`pytest_plugins = ['harvest']` to your conftest.py. But for normal use this should not be required, "
             "installing with pip should be enough.")

    # create the status dictionary for that item
    status_dct = OrderedDict()
    test_status = 'passed'
    test_duration = None
    for k in status_keys:
        statusreport = getattr(item, k)
        status_dct[statusreport.when] = (statusreport.outcome, statusreport.duration)
        # update global test status
        if test_status == 'passed' \
                or (test_status == 'skipped' and statusreport.outcome != 'passed'):
            test_status = statusreport.outcome
        # global test duration is the duration of the "call" step only
        if statusreport.when == "call":
            test_duration = statusreport.duration

    return (test_status, test_duration), status_dct


def get_pytest_params(item):
    """ Returns a dictionary containing item's parameters """

    param_dct = OrderedDict()
    for param_name in item.fixturenames:
        if hasattr(item, 'callspec'):
            if param_name in item.callspec.params:
                # this is a param: ok
                # IMPORTANT: fixture parameters have the same name than the fixtures themselves!
                param_dct[param_name] = item.callspec.params[param_name]
            else:
                # this is a fixture: it is not available by default in item, this is normal pytest behaviour
                # (hence the @saved_fixture decorator)
                pass

    return param_dct
