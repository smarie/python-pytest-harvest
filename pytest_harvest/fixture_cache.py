from collections import OrderedDict
from inspect import isgeneratorfunction

from makefun import with_signature, add_signature_parameters

from pytest_harvest.common import get_scope

try:  # python 3+
    from typing import Union, Any, Dict, Callable
except ImportError:
    pass

try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


def saved_fixture(store='fixture_store',  # type: Union[str, Dict[str, Any]]
                  key=None,               # type: str
                  views=None,             # type: Dict[str, Callable[[Any], Any]]
                  save_raw=None           # type: bool
                  ):
    """
    Decorates a fixture so that it is saved in `store`. `store` can be a dict-like variable or a string
    representing a fixture name to a dict-like session-scoped fixture. By default it uses the global 'fixture_store'
    fixture provided by this plugin.

    After executing all tests, `<store>` will contain a new item under key `<key>` (default is the name of the fixture).
    This item is a dictionary <test_id>: <fixture_value> for each test node.

    ```python
    from random import random

    @saved_fixture('storage')
    @pytest.fixture
    def dummy():
         return random()
    ```

    Users can save additional views created from the fixture instance by applying transforms (callable functions). To
    do this, users can provide a dictionary under the `views` argument, containing a `{<key>: <procedure>}` dict-like.
    For each entry, `<procedure>` will be applied on the fixture instance, and the result will be stored under `<key>`.
    `save_raw` controls whether the fixture instance should still be saved in this case (default: `True` if
    `views is None`, `False` otherwise).

    :param store: a dict-like object or a fixture name corresponding to a dict-like object. in this dictionary, a new
        entry will be added for the fixture. This entry will contain a dictionary <test_id>: <fixture_value> for each
        test node.
    :param key: the name associated with the stored fixture in the store. By default this is the fixture name.
    :param views: an optional dictionary that can be provided to store views created from the fixture, rather than (or
        in addition to, if `save_raw=True`) the fixture itself. The dict should contain a `{<key>: <procedure>}`
        dict-like. For each entry, `<procedure>` will be applied on the fixture instance, and the result will be stored
        under `<key>`.
    :param save_raw: controls whether the fixture instance should be saved. `None` (Default) is an automatic behaviour
        meaning "`True` if `views is None`, `False` otherwise".
    :return: a fixture that will be stored
    """
    # trick to support both with-args and without args usage
    # if only one argument is provided (the first)
    if key is None and views is None and save_raw is None:  # all defaults
        return _saved_fixture(store)
    else:
        return _saved_fixture(store, key, views, save_raw)


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
                       key=None,               # type: str
                       views=None,             # type: Dict[str, Callable[[Any], Any]]
                       save_raw=None           # type: bool
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

    # default: if views is None, we save the raw fixture. If user wants to save views, we do not save the raw
    if save_raw is None:
        save_raw = views is None

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
        scope = get_scope(request)

        if scope != 'function':
            # session- or module-scope
            raise Exception("The `@saved_fixture` decorator is only applicable to function-scope fixtures. `%s`"
                            " seems to have scope='%s'. Consider removing `@saved_fixture` or changing "
                            "the scope to 'function'." % (fixture_fun, scope))

        # Init storage if needed
        if save_raw:
            # init
            if key not in store:
                store[key] = OrderedDict()
            # Check that the node id is unique
            if request.node.nodeid in store[key]:
                raise KeyError("Internal Error - This fixture '%s' was already "
                               "stored for test id '%s'" % (key, request.node.nodeid))

        if views is not None:
            for k in views.keys():
                if k not in store:
                    store[k] = OrderedDict()
                # Check that the node id is unique
                if request.node.nodeid in store[k]:
                    raise KeyError("Internal Error - This fixture view '%s' was already "
                                   "stored for test id '%s'" % (k, request.node.nodeid))

    # We will expose a new signature with additional arguments
    orig_sig = signature(fixture_fun)
    needs_request = 'request' in orig_sig.parameters
    new_args = (Parameter('request', kind=Parameter.POSITIONAL_OR_KEYWORD), ) if not needs_request \
        else () + (Parameter(store, kind=Parameter.POSITIONAL_OR_KEYWORD), ) if store_is_a_fixture else ()
    new_sig = add_signature_parameters(orig_sig, first=new_args)

    # Wrap the fixture in the correct mode (generator or not)
    if not isgeneratorfunction(fixture_fun):
        @with_signature(new_sig)
        def stored_fixture_function(*args, **kwargs):
            """Wraps a fixture so as to store it before it is returned"""
            # get the actual store object
            if store_is_a_fixture:
                store_ = kwargs.pop(store)  # read and remove it
            else:
                # use the variable from outer scope (from `make_saved_fixture`)
                store_ = store
            if needs_request:
                request = kwargs['request']  # read it but leave it there
            else:
                request = kwargs.pop('request')  # read and remove it
            _init_and_check(request, store_)
            fixture_value = fixture_fun(*args, **kwargs)                                        # Get the fixture
            _store_fixture_and_views(store_, request.node.nodeid, key, fixture_value, views, save_raw)  # Store it
            return fixture_value                                                      # Return it

    else:
        @with_signature(new_sig)
        def stored_fixture_function(*args, **kwargs):
            """Wraps a fixture so as to store it before it is returned (generator mode)"""
            # get the actual store object
            if store_is_a_fixture:
                store_ = kwargs.pop(store)
            else:
                # use the variable from outer scope (from `make_saved_fixture`)
                store_ = store
            if needs_request:
                request = kwargs['request']
            else:
                request = kwargs.pop('request')
            _init_and_check(request, store_)
            gen = fixture_fun(*args, **kwargs)
            fixture_value = next(gen)                                                # Get the fixture
            _store_fixture_and_views(store_, request.node.nodeid, key, fixture_value, views, save_raw)  # Store it
            yield fixture_value                                                      # Return it

            # Make sure to terminate the underlying generator
            try:
                next(gen)
            except StopIteration:
                pass

    return stored_fixture_function


def _store_fixture_and_views(store_,
                             node_id,
                             main_key,
                             fixture_value,
                             views,
                             save_raw):
    """

    :param store_:
    :param node_id:
    :param main_key:
    :param fixture_value:
    :param views:
    :param save_raw:
    :return:
    """
    fix_val = _get_underlying_fixture(fixture_value)

    if save_raw:
        # store the fixture value itself
        store_[main_key][node_id] = fix_val

    if views is not None:
        for key, proc in views.items():
            # store each view
            store_[key][node_id] = proc(fix_val)
