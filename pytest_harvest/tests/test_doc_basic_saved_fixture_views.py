import pytest

from pytest_harvest import saved_fixture


@pytest.fixture(params=range(2))
@saved_fixture(views={'other_person_initial': lambda p: p[0], 'other_person_last': lambda p: p[-1]})
def other_person(request):
    """
    A dummy fixture, parametrized so that it has two instances
    """
    if request.param == 0:
        return "world"
    elif request.param == 1:
        return "self"


def test_foo(other_person):
    """
    A dummy test, executed for each `person` fixture available
    """
    print('\n   hello, ' + other_person + ' !')


def test_synthesis(fixture_store):
    """
    In this test we inspect the contents of the fixture store so far,
    and check that the 'person' entry contains a dict <test_id>: <person>
    """
    # print the keys in the store
    print("\n   Available `fixture_store` keys:")
    for k in fixture_store:
        print("    - '%s'" % k)

    # we used save_raw=False so the fixture itself is not stored
    assert 'other_person' not in fixture_store

    # however the views are stored
    assert 'other_person_initial' in fixture_store
    assert set(fixture_store['other_person_initial'].values()) == {'w', 's'}
    assert set(fixture_store['other_person_last'].values()) == {'d', 'f'}
