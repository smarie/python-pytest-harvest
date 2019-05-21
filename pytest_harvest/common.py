import pytest


HARVEST_PREFIX = "harvest_rep_"


# def get_fixture_name(fixture_fun):
#     """
#     Internal utility to retrieve the fixture name corresponding to the given fixture function .
#     Indeed there is currently no pytest API to do this.
#
#     :param fixture_fun:
#     :return:
#     """
#     custom_fixture_name = getattr(fixture_fun._pytestfixturefunction, 'name', None)
#
#     if custom_fixture_name is not None:
#         # there is a custom fixture name
#         return custom_fixture_name
#     else:
#         obj__name = getattr(fixture_fun, '__name__', None)
#         if obj__name is not None:
#             # a function, probably
#             return obj__name
#         else:
#             # a callable object probably
#             return str(fixture_fun)


def get_fixture_value(request, fixture_name):
    """
    Returns the value associated with fixture named `fixture_name`, in provided `request` context.
    This is just an easy way to use `getfixturevalue` or `getfuncargvalue` according to whichever is available in
    current `pytest` version.

    :param request:
    :param fixture_name:
    :return:
    """
    try:
        # Pytest 4+ or latest 3.x (to avoid the deprecated warning)
        return request.getfixturevalue(fixture_name)
    except AttributeError:
        # Pytest 3-
        return request.getfuncargvalue(fixture_name)


# Create a symbol that will work to create a fixture containing 'yield', whatever the pytest version
if int(pytest.__version__.split('.', 1)[0]) < 3:
    yield_fixture = pytest.yield_fixture
else:
    yield_fixture = pytest.fixture


def get_scope(request):
    """
    Utility method to return the scope of a pytest request
    :param request:
    :return:
    """
    if request.node is request.session:
        return 'session'
    elif hasattr(request.node, 'function'):
        return 'function'
    else:
        return 'module'
