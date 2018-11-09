from collections import OrderedDict
from warnings import warn

from pytest_harvest.plugin import HARVEST_PREFIX


PYTEST_OBJ_NAME = 'pytest_obj'


def get_session_synthesis_dct(session):

    res_dct = OrderedDict()
    for item in session.items:
        item_dct = dict()

        # Fill the dictionary with information about this test node
        # -- test object
        item_dct[PYTEST_OBJ_NAME] = item.obj

        # -- test status: this information is available thanks to our hook in harvest plugin
        status_keys = [k for k in vars(item) if k.startswith(HARVEST_PREFIX)]
        if len(status_keys) == 0:
            warn("[pytest-harvest] Test items status is not available. You should maybe install pytest-harvest with "
                 "pip. If it is already the case, you case try to force-use it by adding "
                 "`pytest_plugins = ['harvest']` to your conftest.py. But for normal use this should not be required, "
                 "installing with pip should be enough.")
        status_dct = dict()
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

        item_dct["pytest_status"] = test_status
        item_dct["pytest_duration"] = test_duration
        item_dct["pytest_status_details"] = status_dct

        # -- parameters (of tests and fixtures)
        param_dct = dict()
        for param_name in item.fixturenames:
            if hasattr(item, 'callspec'):
                if param_name in item.callspec.params:
                    # this is a param: ok
                    # IMPORTANT: fixture parameters have the same name than the fixtures themselves!
                    param_dct[param_name] = item.callspec.params[param_name]
                else:
                    # this is a fixture: it is not saved, this is normal (hence the storage decorator)
                    pass
        item_dct["pytest_params"] = param_dct

        # For info: https://docs.pytest.org/en/latest/_modules/_pytest/runner.html
        # used_fixtures = sorted(item._fixtureinfo.name2fixturedefs.keys())
        # if used_fixtures:
        #     tw.write(" (fixtures used: {})".format(", ".join(used_fixtures)))

        # Finally store in the main dictionary
        res_dct[item.nodeid] = item_dct

    return res_dct
