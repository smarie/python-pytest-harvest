from collections import OrderedDict
from inspect import isgeneratorfunction

from decopatch import DECORATED, function_decorator
from makefun import wraps, add_signature_parameters

from pytest_harvest.common import get_scope

try:  # python 3+
    from typing import Union, Any, Dict, Callable
except ImportError:
    pass

try:  # python 3.3+
    from inspect import signature, Parameter
except ImportError:
    from funcsigs import signature, Parameter


@function_decorator
def saved_fixture(store='fixture_store',  # type: Union[str, Dict[str, Any]]
                  key=None,               # type: str
                  views=None,             # type: Dict[str, Callable[[Any], Any]]
                  save_raw=None,          # type: bool
                  fixture_fun=DECORATED
                  ):
    """
    Decorates a fixture so that it is saved in `store`. `store` can be a dict-like variable or a string
    representing a fixture name to a dict-like session-scoped fixture. By default it uses the global 'fixture_store'
    fixture provided by this plugin.

    After executing all tests, `<store>` will contain a new item under key `<key>` (default is the name of the fixture).
    This item is a dictionary <test_id>: <fixture_value> for each test node where the fixture was setup.

    ```python
    import pytest
    from pytest_harvest import saved_fixture

    @pytest.fixture
    @saved_fixture
    def dummy():
        return 1

    def test_dummy(dummy):
        pass

    def test_synthesis(fixture_store):
        print(fixture_store['dummy'])
    ```

    Note that for session-scoped and module-scoped fixtures, not all test ids will appear in the store - only those
    for which the fixture was (re)created.

    Users can save additional views created from the fixture instance by applying transforms (callable functions). To
    do this, users can provide a dictionary under the `views` argument, containing a `{<key>: <procedure>}` dict-like.
    For each entry, `<procedure>` will be applied on the fixture instance, and the result will be stored under `<key>`.
    `save_raw` controls whether the fixture instance should still be saved in this case (default: `True` if
    `views is None`, `False` otherwise).

    :param store: a dict-like object or a fixture name corresponding to a dict-like object. in this dictionary, a new
        entry will be added for the fixture. This entry will contain a dictionary <test_id>: <fixture_value> for each
        test node. By default fixtures are stored in the `fixture_store``fixture.
    :param key: the name associated with the stored fixture in the store. By default this is the fixture name.
    :param views: an optional dictionary that can be provided to store views created from the fixture, rather than (or
        in addition to, if `save_raw=True`) the fixture itself. The dict should contain a `{<key>: <procedure>}`
        dict-like. For each entry, `<procedure>` will be applied on the fixture instance, and the result will be stored
        under `<key>`.
    :param save_raw: controls whether the fixture instance should be saved. `None` (Default) is an automatic behaviour
        meaning "`True` if `views is None`, `False` otherwise".
    :return: a fixture that will be stored
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
        """Performs a few checks and returns the key to use for saving (the node id)"""
        # find the current node id depending on the scope
        scope = get_scope(request)
        if scope == 'function':
            nodeid = request.node.nodeid
        else:
            # session- or module-scope
            # raise Exception("The `@saved_fixture` decorator is only applicable to function-scope fixtures. `%s`"
            #                 " seems to have scope='%s'. Consider removing `@saved_fixture` or changing "
            #                 "the scope to 'function'." % (fixture_fun, scope))
            nodeid = request._pyfuncitem.nodeid

        # Init storage if needed
        if save_raw:
            # init
            if key not in store:
                store[key] = OrderedDict()
            # Check that the node id is unique
            if nodeid in store[key]:
                raise KeyError("Internal Error - This fixture '%s' was already "
                               "stored for test id '%s'" % (key, nodeid))

        if views is not None:
            for k in views.keys():
                if k not in store:
                    store[k] = OrderedDict()
                # Check that the node id is unique
                if nodeid in store[k]:
                    raise KeyError("Internal Error - This fixture view '%s' was already "
                                   "stored for test id '%s'" % (k, nodeid))

        return nodeid

    # We will expose a new signature with additional arguments
    orig_sig = signature(fixture_fun)
    func_needs_request = 'request' in orig_sig.parameters
    new_args = ((Parameter('request', kind=Parameter.POSITIONAL_OR_KEYWORD),) if not func_needs_request else ()) \
               + ((Parameter(store, kind=Parameter.POSITIONAL_OR_KEYWORD),) if store_is_a_fixture else ())
    new_sig = add_signature_parameters(orig_sig, first=new_args)

    # Wrap the fixture in the correct mode (generator or not)
    if not isgeneratorfunction(fixture_fun):
        @wraps(fixture_fun, new_sig=new_sig)
        def stored_fixture_function(*args, **kwargs):
            """Wraps a fixture so as to store it before it is returned"""
            # get the actual store object
            if store_is_a_fixture:
                store_ = kwargs.pop(store)  # read and remove it
            else:
                # use the variable from outer scope (from `make_saved_fixture`)
                store_ = store
            request = kwargs['request'] if func_needs_request else kwargs.pop('request')
            nodeid = _init_and_check(request, store_)
            fixture_value = fixture_fun(*args, **kwargs)                                        # Get the fixture
            _store_fixture_and_views(store_, nodeid, key, fixture_value, views, save_raw)  # Store it
            return fixture_value                                                      # Return it

    else:
        @wraps(fixture_fun, new_sig=new_sig)
        def stored_fixture_function(*args, **kwargs):
            """Wraps a fixture so as to store it before it is returned (generator mode)"""
            # get the actual store object
            if store_is_a_fixture:
                store_ = kwargs.pop(store)
            else:
                # use the variable from outer scope (from `make_saved_fixture`)
                store_ = store
            request = kwargs['request'] if func_needs_request else kwargs.pop('request')
            nodeid = _init_and_check(request, store_)
            gen = fixture_fun(*args, **kwargs)
            fixture_value = next(gen)                                                # Get the fixture
            _store_fixture_and_views(store_, nodeid, key, fixture_value, views, save_raw)  # Store it
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


def _get_underlying_fixture(f):
    try:
        from pytest_steps.steps_generator import get_underlying_fixture
        return get_underlying_fixture(f)
    except ImportError:
        return f
