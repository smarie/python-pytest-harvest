import pytest


HARVEST_PREFIX = "harvest_rep_"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    We use this hook to store the test execution status for each node in the 'item' object,
    so that we can use it in `get_session_synthesis_dct`

    It is called because the whole package is a pytest plugin (it has a pytest entry point in setup.py)

    Following the example here:
    https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures

    :param item:
    :param call:
    :return:
    """
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, HARVEST_PREFIX + rep.when, rep)
