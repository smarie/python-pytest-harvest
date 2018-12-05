import pytest


@pytest.mark.parametrize('p', ['world', 'self'], ids=str)
def test_foo(p):
    print('hello, ' + p)


def test_synthesis(module_results_dct):
    # print the keys in the dictionary
    print(list(module_results_dct.keys()))

    # print the contents of an entry
    print(dict(module_results_dct['test_foo[world]']))
