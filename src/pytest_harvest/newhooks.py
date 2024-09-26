"""
xdist hooks.

Additionally, pytest-xdist will also decorate a few other hooks
with the worker instance that executed the hook originally:

``pytest_runtest_logreport``: ``rep`` parameter has a ``node`` attribute.

You can use this hooks just as you would use normal pytest hooks, but some care
must be taken in plugins in case ``xdist`` is not installed. Please see:

    http://pytest.org/en/latest/writing_plugins.html#optionally-using-hooks-from-3rd-party-plugins
"""
import pytest


@pytest.mark.firstresult
def pytest_harvest_xdist_init():
    """ called when xdist distribution is enabled, when pytest master node session starts, so that plugin can init.
    Plugins should return `True` if success so as to bypass the default strategy."""


@pytest.mark.firstresult
def pytest_harvest_xdist_worker_dump(worker_id, session_items, fixture_store):
    """ called when xdist distribution is enabled, when xdist worker session ends. Plugin should persist
    `session_items` and `fixture_store` and return `True` if successful so as to bypass the default strategy."""


@pytest.mark.firstresult
def pytest_harvest_xdist_load():
    """ called when xdist distribution is enabled, on xdist master, the first time pytest-harvest needs to access
    persisted information. Should return a dictionary {worker_id: (session_items, fixture_store)}"""


@pytest.mark.firstresult
def pytest_harvest_xdist_cleanup():
    """ called when xdist distribution is enabled, on xdist master, when session ends. Plugins should cleanup and
    return True to prevent the default strategy to run"""
