from collections import OrderedDict
from inspect import isgeneratorfunction

from pytest_harvest.decorator_hack import my_decorate


try:  # python 3+
    from typing import Union, Any, Dict
except ImportError:
    pass


def saved_fixture(store='fixture_store',  # type: Union[str, Dict[str, Any]]
                  key=None                # type: str
                  ):
    """
    Decorates a fixture so that it is saved in `store`. `store` can be a dict-like variable or a string
    representing a fixture name to a dict-like session-scoped fixture. By default it uses the global 'fixture_store'
    fixture provided by this plugin.

    After executing all tests, <store> will contain a new item under key <name>. This item is a dictionary
    <test_id>: <fixture_value> for each test node.

    ```python
    from random import random

    @saved_fixture('storage')
    @pytest.fixture
    def dummy():
         return random()
    ```

    :param store: a dict-like object or a fixture name corresponding to a dict-like object. in this dictionary, a new
        entry will be added for the fixture. This entry will contain a dictionary <test_id>: <fixture_value> for each
        test node.
    :param key: the name associated with the stored fixture in the store. By default this is the fixture name.
    :return: a fixture that will be stored
    """
    # trick to support both with-args and without args usage
    # if only one argument is provided (the first)
    if key is None:
        return _saved_fixture(store)
    else:
        return _saved_fixture(store, key)


def _saved_fixture(*args, **kwargs):
    """ Inner decorator creation method to support no-arg calls """
    if len(args) == 1 and callable(args[0]):
        # called without arguments, directly decorates a function
        f = args[0]
        return make_saved_fixture(f)
    else:
        # return a function decorator
        def _decorator(f):
            return make_saved_fixture(f, *args, **kwargs)
        return _decorator


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


def _get_underlying_fixture(f):
    try:
        from pytest_steps.steps_generator import get_underlying_fixture
        return get_underlying_fixture(f)
    except ImportError:
        return f


def make_saved_fixture(fixture_fun,
                       store='fixture_store',  # type: Union[str, Dict[str, Any]]
                       key=None                # type: str
                       ):
    """
    Manual decorator to decorate a (future) fixture function so that it is saved in a storage.

    ```python
    def f():
        return "dummy"

    # manually declare that it should be saved
    f = make_saved_fixture(f)

    # manually make a fixture from f
    f = pytest.fixture(f)
    ```

    See `@saved_fixture` decorator for parameter details.
    """

    # Simply get the function name
    fixture_name = getattr(fixture_fun, '__name__', None) or str(fixture_fun)

    # Name to use for storage
    key = key or fixture_name

    # is the store a fixture or an object ?
    store_is_a_fixture = isinstance(store, str)

    # if the store object is already available, we can ensure that it is initialized. Otherwise trust pytest for that
    if not store_is_a_fixture:
        if key in store.keys():
            raise ValueError("Key '%s' already exists in store object. Please make sure that your store object is "
                             "properly initialized as an empty dict-like object, and/or provide a different custom "
                             "`name` if two stored fixtures share the same storage key name.")

    # Note: we can not init the storage[key] entry here because when storage is a fixture, it does not yet exist.

    def _init_and_check(request, store):
        # Init storage if needed
        if key not in store:
            store[key] = OrderedDict()
        # Check that the node id is unique
        if request.node.nodeid in store[key]:
            raise KeyError("Internal Error - This fixture '%s' was already "
                           "stored for test id '%s'" % (key, request.node.nodeid))

    # Wrap the fixture in the correct mode (generator or not)
    if not isgeneratorfunction(fixture_fun):
        def fixture_wrapper(f, request, *args, **kwargs):
            """Wraps a fixture so as to store it before it is returned"""
            # get the actual store object
            if store_is_a_fixture:
                store_ = args[0]
                args = args[1:]
            else:
                # use the variable from outer scope (from `make_saved_fixture`)
                store_ = store
            _init_and_check(request, store_)
            fixture_value = f(*args, **kwargs)                                        # Get the fixture
            store_[key][request.node.nodeid] = _get_underlying_fixture(fixture_value)  # Store it
            return fixture_value                                                      # Return it

    else:
        def fixture_wrapper(f, request, *args, **kwargs):
            """Wraps a fixture so as to store it before it is returned (generator mode)"""
            # get the actual store object
            if store_is_a_fixture:
                store_ = args[0]
                args = args[1:]
            else:
                # use the variable from outer scope (from `make_saved_fixture`)
                store_ = store
            _init_and_check(request, store_)
            gen = f(*args, **kwargs)
            fixture_value = next(gen)                                                # Get the fixture
            store_[key][request.node.nodeid] = _get_underlying_fixture(fixture_value)  # Store it
            yield fixture_value                                                      # Return it

            # Make sure to terminate the underlying generator
            try:
                next(gen)
            except StopIteration:
                pass

    if store_is_a_fixture:
        # add 'store' as second positional argument
        stored_fixture_function = my_decorate(fixture_fun, fixture_wrapper, additional_args=('request', store))
    else:
        stored_fixture_function = my_decorate(fixture_fun, fixture_wrapper, additional_args=('request', ))

    return stored_fixture_function
