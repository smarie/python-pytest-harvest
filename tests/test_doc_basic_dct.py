import time

import pytest


@pytest.mark.parametrize('p', ['world', 'self'], ids=str)
def test_foo(p):
    """
    A dummy test, parametrized so that it is executed twice
    """
    print('\n   hello, ' + p + ' !')
    time.sleep(len(p) / 10)


def test_synthesis(module_results_dct):
    """
    In this test we just look at the synthesis of all tests
    executed before it, in that module.
    """
    # print the keys in the synthesis dictionary
    print("\n   Available `module_results_dct` keys:")
    for k in module_results_dct:
        print("    - " + k)

    # print what is available for a single test
    print("\n   Contents of 'test_foo[world]':")
    for k, v in module_results_dct['test_foo[world]'].items():
        if k != 'status_details':
            print("    - '%s': %s" % (k, v))
        else:
            print("    - '%s':" % k)
            for kk, vv in v.items():
                print("      - '%s': %s" % (kk, vv))
