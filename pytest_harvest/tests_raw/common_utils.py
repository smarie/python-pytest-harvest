import pytest

if int(pytest.__version__.split('.', 1)[0]) >= 3:
    yield_fixture = pytest.yield_fixture
else:
    yield_fixture = pytest.fixture
