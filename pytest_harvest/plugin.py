from collections import OrderedDict

import pytest
import six

try: # python 3.5+
    from typing import Union, Iterable, Mapping, Any
except ImportError:
    pass

from pytest_harvest.common import HARVEST_PREFIX
from pytest_harvest.results_bags import create_results_bag_fixture
from pytest_harvest.results_session import get_session_synthesis_dct


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


# ------------- To collect benchmark results ------------
FIXTURE_STORE = OrderedDict()
"""The default fixture store, that is also available through the `fixture_store` fixture."""


@pytest.fixture(scope='session')  # no need for autouse=True
def fixture_store():
    """
    A "fixture store" fixture: a dictionary where fixture instances can be saved.

    By default

     - all fixtures decorated with `@saved_fixture` are saved in this store.
     - the `results_bag` fixture is also saved in this store.

    To retrieve the contents of the store, you can:

     * create a test using this fixture and make sure that it is executed after all others.
     * access this fixture from a dependent fixture and read its value in the setup or teardown script.
     * access this fixture from the `request` fixture using the `get_fixture_value` helper method.
     * access the `FIXTURE_STORE` symbol directly

    This fixture has session scope so it is unique across the whole session.
    """
    return FIXTURE_STORE


results_bag = create_results_bag_fixture('fixture_store', name='results_bag')
"""
A "results bag" fixture: a dictionary where you can store anything (results, context, etc.) during your tests execution.
It offers a "much"-like api: you can access all entries using the object protocol such as in `results_bag.a = 1`.

This fixture has function-scope so a new, empty instance is injected in each test node. 

There are several ways to gather all results after they have been stored. 

 * To get the raw stored results, use the `fixture_store` fixture: `fixture_store['results_bag']` will contain all 
   result bags for all tests.
   
 * If you are interested in both the stored results AND some stored fixture values (through `@saved_fixture`), you 
   might rather wish to leverage the following helpers:

     - use one of the `session_results_dct`, `module_results_dct`, `session_results_df` or `module_results_df` 
       fixtures. They contain all available information, in a nicely summarized way.
       
     - use the `get_session_synthesis_dct(session)` helper method to create a similar synthesis than the above with 
       more customization capabilities.

If you wish to create custom results bags similar to this one (for example to create several with different names), 
use `create_results_bag_fixture`.
"""


def get_session_results_dct(session_or_request,
                            fixture_store=FIXTURE_STORE,            # type: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]
                            results_bag_fixture_name='results_bag'  # type: str
                            ):
    # type: (...) -> Mapping[str, Mapping[str, Any]]
    """
    Helper method to get exactly the same object than the `session_results_dct` fixture, from a session object.
    This can be useful to retrieve the results from the `pytest_sessionfinish` hook for example.

    See `session_results_dct` fixture for details.

    :param session_or_request: the pytest session or request
    :param fixture_store: an optional fixture store
    :param results_bag_fixture_name: an optional name for results bag fixture in the fixture store. Default is
            "results_bag"
    :return:
    """
    results_dct = get_session_synthesis_dct(session_or_request, durations_in_ms=True,
                                            test_id_format='full', status_details=True, pytest_prefix=False,
                                            fixture_store=fixture_store,
                                            flatten=False, flatten_more=results_bag_fixture_name)

    # We do not want to post-process according to steps here, this fixture should have as a contract that the keys
    # are the True test ids.
    # try:
    #     # if pytest_steps is installed, separate the test ids from the step ids
    #     from pytest_steps import handle_steps_in_synthesis_dct
    #     results_dct = handle_steps_in_synthesis_dct(results_dct, is_flat=False)
    # except ImportError:
    #     # pytest_steps is not installed, ok.
    #     pass

    return results_dct


@pytest.fixture(scope='function')
def session_results_dct(request, fixture_store):
    # type: (...) -> Mapping[str, Mapping[str, Any]]
    """
    This fixture contains a synthesis dictionary for all tests completed "so far", with 'full' id format. It includes
    contents from the default `fixture_store`, including `results_bag`.

    Behind the scenes it relies on `get_session_synthesis_dct`.

    This fixture has a function scope because we want its contents to be refreshed every time it is needed.
    """
    return get_session_results_dct(request.session, fixture_store=fixture_store)


def get_module_results_dct(session_or_request,
                           module_name,                            # type: str
                           fixture_store=FIXTURE_STORE,            # type: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]
                           results_bag_fixture_name='results_bag'  # type: str
                           ):
    # type: (...) -> Mapping[str, Mapping[str, Any]]
    """
    Helper method to get exactly the same object than the `module_results_dct` fixture, from a session object.
    This can be useful to retrieve the results from the `pytest_sessionfinish` hook for example.

    See `module_results_dct` fixture for details.

    :param session_or_request: the pytest session or request
    :param module_name: a string representing the module name to filter on
    :param fixture_store: an optional fixture store
    :param results_bag_fixture_name: an optional name for results bag fixture in the fixture store. Default is
        "results_bag"
    :return:
    """
    results_dct = get_session_synthesis_dct(session_or_request, durations_in_ms=True,
                                            filter=module_name, pytest_prefix=False,
                                            test_id_format='function', status_details=True,
                                            fixture_store=fixture_store,
                                            flatten=False, flatten_more=results_bag_fixture_name)

    # We do not want to post-process according to steps here, this fixture should have as a contract that the keys
    # are the True test ids.
    #
    # try:
    #     # if pytest_steps is installed, separate the test ids from the step ids
    #     from pytest_steps import handle_steps_in_synthesis_dct
    #     results_dct = handle_steps_in_synthesis_dct(results_dct, is_flat=False)
    # except ImportError:
    #     # pytest_steps is not installed, ok.
    #     pass

    return results_dct


@pytest.fixture(scope='function')
def module_results_dct(request, fixture_store):
    # type: (...) -> Mapping[str, Mapping[str, Any]]
    """
    This fixture returns a synthesis dictionary for all tests completed "so far" in the module of the caller,
    with 'function' id format. It includes contents from the default `fixture_store`, including `results_bag`.

    Behind the scenes it relies on `get_session_synthesis_dct`.

    This fixture has a function scope because we want its contents to be refreshed every time it is needed.
    """
    return get_module_results_dct(request, module_name=request.module.__name__, fixture_store=fixture_store)


try:
    import pandas as pd

    def get_session_results_df(session_or_request,
                               fixture_store=FIXTURE_STORE,            # type: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]
                               results_bag_fixture_name='results_bag'  # type: str
                               ):
        # type: (...) -> pd.DataFrame
        """
        Helper method to get exactly the same object than the `session_results_df` fixture, from a session object.
    This can be useful to retrieve the results from the `pytest_sessionfinish` hook for example.

    See `session_results_df` fixture for details.

        :param session_or_request: the pytest session or request
        :param fixture_store: an optional fixture store
        :param results_bag_fixture_name: an optional name for results bag fixture in the fixture store. Default is
            "results_bag"
        :return:
        """

        # get the synthesis dictionary, merged with default fixture store and flattening default results_bag
        session_results_dct = get_session_synthesis_dct(session_or_request, durations_in_ms=True,
                                                        test_id_format='full', status_details=False,
                                                        fixture_store=fixture_store,
                                                        flatten=True, flatten_more=results_bag_fixture_name)

        # convert to a pandas dataframe
        results_df = pd.DataFrame.from_dict(session_results_dct, orient='index')
        results_df = results_df.loc[list(session_results_dct.keys()), :]  # fix rows order
        results_df.index.name = 'test_id'  # set index name

        # We do not want to post-process according to steps here, this fixture should have as a contract that the keys
        # are the True test ids.
        #
        # try:
        #     # if pytest_steps is installed, separate the test ids from the step ids
        #     from pytest_steps import handle_steps_in_results_df
        #     results_df = handle_steps_in_results_df(results_df, keep_orig_id=True, no_steps_policy='skip')
        # except ImportError:
        #     # pytest_steps is not installed, ok.
        #     pass
        # except Exception as e:
        #     # other issue: warn about it but continue
        #     warn("%s: %s" % (e, type(e)))

        return results_df

except ImportError as e:
    def get_session_results_df(*args, **kwargs):
        six.raise_from(Exception("There was an error importing `pandas` module. Fixture `session_results_df` and method"
                                 "`get_session_results_df` can not be used in this session."), e)


@pytest.fixture(scope='function')
def session_results_df(request, fixture_store):
    """
    This fixture contains a synthesis dataframe for all tests completed "so far" in the module of the caller,
    with 'function' id format. It includes contents from the default `fixture_store`, including `results_bag`.

    It is basically just a transformation of the `session_results_dct` fixture into a pandas `DataFrame`.

    If `pytest-steps` is installed, the step ids will be extracted and the dataframe index will be multi-level
    (test id without step, step id).

    This fixture has a function scope because we want its contents to be refreshed every time it is needed.
    """
    return get_session_results_df(request, fixture_store=fixture_store)


try:
    import pandas as pd

    def get_filtered_results_df(session,
                                filter=None,                            # type: Any
                                test_id_format='full',                  # type: str
                                fixture_store=FIXTURE_STORE,            # type: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]
                                results_bag_fixture_name='results_bag'  # type: str
                                ):
        # type: (...) -> pd.DataFrame
        """
        Combines `get_session_synthesis_dct` with a transformation into a pandas DataFrame.

        :param session: the pytest session object
        :param filter: any filter, see `get_session_synthesis_dct` for details
        :param fixture_store: an optional fixture store
        :param results_bag_fixture_name: an optional name for results bag fixture in the fixture store. Default is
            "results_bag"
        :return:
        """
        # get the synthesis dictionary, merged with default fixture store and flattening default results_bag
        module_results_dct = get_session_synthesis_dct(session, durations_in_ms=True,
                                                       filter=filter,
                                                       test_id_format=test_id_format, status_details=False,
                                                       fixture_store=fixture_store,
                                                       flatten=True, flatten_more=results_bag_fixture_name)

        # convert to a pandas dataframe
        results_df = pd.DataFrame.from_dict(module_results_dct, orient='index')
        results_df = results_df.loc[list(module_results_dct.keys()), :]  # fix rows order
        results_df.index.name = 'test_id'  # set index name

        # We do not want to post-process according to steps here, this fixture should have as a contract that the keys
        # are the True test ids.
        #
        # try:
        #     # if pytest_steps is installed, separate the test ids from the step ids
        #     from pytest_steps import handle_steps_in_results_df
        #     results_df = handle_steps_in_results_df(results_df, keep_orig_id=True, no_steps_policy='skip')
        # except ImportError:
        #     # pytest_steps is not installed, ok.
        #     pass
        # except Exception as e:
        #     # other issue: warn about it but continue
        #     warn("%s: %s" % (e, type(e)))

        return results_df

except ImportError as e:
    def get_filtered_results_df(*args, **kwargs):
        six.raise_from(Exception("There was an error importing `pandas` module. Fixture `session_results_df` and "
                                 "methods `get_filtered_results_df` and `get_module_results_df` can not be used in this"
                                 " session. "), e)


def get_module_results_df(session,
                          module_name,                            # type: str
                          fixture_store=FIXTURE_STORE,            # type: Union[Mapping[str, Any], Iterable[Mapping[str, Any]]]
                          results_bag_fixture_name='results_bag'  # type: str
                          ):
    """
    Helper method to get exactly the same object than the `module_results_df` fixture, from a session object.
    This can be useful to retrieve the results from the `pytest_sessionfinish` hook for example.

    See `module_results_df` fixture for details.

    :param session: the pytest session object
    :param module_name: the name of the module
    :param fixture_store: an optional fixture store
    :param results_bag_fixture_name: an optional name for results bag fixture in the fixture store. Default is
        "results_bag"
    :return:
    """
    return get_filtered_results_df(session=session, test_id_format='function', filter=module_name,
                                   fixture_store=fixture_store, results_bag_fixture_name=results_bag_fixture_name)


@pytest.fixture(scope='function')
def module_results_df(request, fixture_store):
    """
    This fixture returns a synthesis dataframe for all tests completed "so far" in the module of the caller,
    with 'function' id format. It includes contents from the default `fixture_store`, including `results_bag`.

    It is basically just a transformation of the `module_results_dct` fixture into a pandas DataFrame.

    If `pytest-steps` is installed, the step ids will be extracted and the dataframe index will be multi-level
    (test id without step, step id).

    This fixture has a function scope because we want its contents to be refreshed every time it is needed.
    """
    return get_module_results_df(request.session, module_name=request.module.__name__, fixture_store=fixture_store)
