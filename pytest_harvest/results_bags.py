from datetime import datetime

import pytest
from six import raise_from

try:  # python 3+
    from typing import Type, Set, Union, Any, Dict
except ImportError:
    pass

try:
    from pytest_harvest import one_per_step
except ImportError:
    # pytest steps not installed: define as a transparent decorator
    def one_per_step(f):
        return f

from pytest_harvest.common import yield_fixture
from pytest_harvest.fixture_cache import saved_fixture


class ResultsBag(dict):
    """
    A simple 'Munch', that is, a dual object/dict.
    It is hashable with a not very interesting hash, but at least a unique one in a python session (id(self))
    """

    # object
    def __setattr__(self, key, value):
        # try:  No exception can happen: key is always a string, and new entries are allowed in a dict
        self[key] = value
        # except KeyError as e:
        #     raise_from(AttributeError(key), e)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise_from(AttributeError(key), e)

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as e:
            raise_from(AttributeError(key), e)

    # object base
    def __str__(self):
        return dict.__str__(self)

    def __repr__(self):
        return "ResultsBag:\n" + dict.__repr__(self)

    def __hash__(self):
        """Make the type hashable with a fake hash"""
        return id(self)


# Just to be sure
assert isinstance(ResultsBag(), dict)


def _results_bag_fixture_impl(bag_type=None,                  # type: Type[Any]
                              ):
    """
    Implementation of a results bag fixture. It creates a `ResultsBag` by default, or an object of custom `bag_type`.

    Note: we do not measure time here anymore because it is less precise than pytest duration

    :param bag_type: the type of object to create as results bag. Default: `ResultsBag`
    :return:
    """

    # Create the results bag
    bag_type = ResultsBag if bag_type is None else bag_type
    results_bag = bag_type()

    # Yield it - note: we do not measure time anymore because it is less precise than pytest duration
    # start = datetime.now()
    yield results_bag
    # end = datetime.now()

    # Fill execution time
    # results_bag[exec_time_key] = (end - start).total_seconds()


def create_results_bag_fixture(storage,                        # type: Union[str, Dict[str, Any]]
                               name='results_bag',             # type: str
                               bag_type=None,                  # type: Type[Any]
                               ):
    """
    Creates a "results bag" fixture with name <name> stored in the given storage (under key=<name>). By default results
    bags are instances of `ResultsBag` but you can provide another `bag_type` if needed.

    :param storage: a dict-like object or a fixture name corresponding to a dict-like object. in this dictionary, a new
        entry will be added for the fixture. This entry will contain a dictionary <test_id>: <fixture_value> for each
        test node.
    :param name: the name associated with the stored fixture in the global storage. By default this is 'results_bag'.
    :param bag_type: the type of object to create as a results bag. Default: `ResultsBag`
    :return:
    """
    # Create the same function than _results_bag_fixture_impl but with preset arguments (same than functools.partial)
    def _results_bag():
        gen = _results_bag_fixture_impl(bag_type=bag_type)
        for res in gen:
            yield res

    # Create one result bag per step if needed (if pytest_harvest is present)
    _results_bag = one_per_step(_results_bag)

    # Declare that this fixture should be saved
    _results_bag = saved_fixture(storage, key=name)(_results_bag)

    # Decorate manually as a fixture
    _results_bag.__name__ = name
    results_bag_fixture = yield_fixture(_results_bag)

    return results_bag_fixture
