import pytest

from pytest_harvest import saved_fixture


@pytest.fixture(params=range(2))
@saved_fixture
def person(request):
    """
    A dummy fixture, parametrized so that it has two instances
    """
    if request.param == 0:
        return "world"
    elif request.param == 1:
        return "self"


def test_foo(person):
    """
    A dummy test, executed for each `person` fixture available
    """
    print('\n   hello, ' + person + ' !')


def test_synthesis(fixture_store):
    """
    In this test we inspect the contents of the fixture store so far,
    and check that the 'person' entry contains a dict <test_id>: <person>
    """
    # print the keys in the store
    print("\n   Available `fixture_store` keys:")
    for k in fixture_store:
        print("    - '%s'" % k)

    # print what is available for the 'person' entry
    print("\n   Contents of `fixture_store['person']`:")
    for k, v in fixture_store['person'].items():
        print("    - '%s': %s" % (k, v))
