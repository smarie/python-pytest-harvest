import time

import pytest


@pytest.mark.parametrize('p', ['world', 'self'], ids=str)
def test_foo(p):
    """
    A dummy test, parametrized so that it is executed twice
    """
    print('\n   hello, ' + p + ' !')
    time.sleep(len(p) / 10)


def test_synthesis(module_results_df):
    """
    In this test we just look at the synthesis of all tests
    executed before it, in that module.
    """
    # print the synthesis dataframe
    print("\n   `module_results_df` dataframe:\n")
    print(module_results_df)
