from datetime import datetime

import pytest


@pytest.mark.parametrize('p', ['world', 'self'], ids=str)
def test_foo(p, results_bag):
    """
    A dummy test, parametrized so that it is executed twice
    """
    print('\n   hello, ' + p + ' !')

    # Let's store some things in the results bag
    results_bag.nb_letters = len(p)
    results_bag.current_time = datetime.now().isoformat()


def test_synthesis(fixture_store):
    """
    In this test we just look at the synthesis of all tests
    executed before it, in that module.
    """
    # print the keys in the store
    print("\n   Available `fixture_store` keys:")
    for k in fixture_store:
        print("    - '%s'" % k)

    # print what is available for the 'results_bag' entry
    print("\n   Contents of `fixture_store['results_bag']`:")
    for k, v in fixture_store['results_bag'].items():
        print("    - '%s':" % k)
        for kk, vv in v.items():
            print("      - '%s': %s" % (kk, vv))
