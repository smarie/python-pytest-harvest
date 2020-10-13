import pytest
from distutils.version import LooseVersion

from pytest_cases import lazy_value, fixture_ref, parametrize, fixture

from pytest_harvest import get_session_synthesis_dct


pytest2 = LooseVersion(pytest.__version__) < LooseVersion("3.0.0")


@fixture
def b():
    return 1, "hello"


def foo():
    return ["r", 1]


@parametrize("a", [lazy_value(foo),
                   # fixture_ref(b)
                   ])
def test_foo(a):
    """a single lazy value"""
    assert a in (["r", 1], (1, "hello"))


@parametrize("i,j", [lazy_value(foo),
                     # fixture_ref(b)
                     ])
def test_foo2(i, j):
    """a lazy value used as a tuple containing several args"""
    assert i, j in (("r", 1), (1, "hello"))


@parametrize("a", [lazy_value(foo),
                   fixture_ref(b)
                   ])
def test_foo3(a, results_bag):
    """a lazy value transformed by pytest-cases into a fixture because another parameter uses a fixture reference"""
    assert a in (["r", 1], (1, "hello"))

    # in that case the only workaround is to use the results bag
    # to store explicitly the values, see https://github.com/smarie/python-pytest-harvest/issues/44
    results_bag.a_value = a


def test_synthesis(request, module_results_df):
    # manual test
    dct = get_session_synthesis_dct(request, filter=test_foo, test_id_format="function")
    assert len(dct) == 1
    a_param = dct["test_foo[foo]"]["pytest_params"]["a"]
    assert not isinstance(a_param, int)
    assert str(a_param) == "foo"

    dct = get_session_synthesis_dct(request, filter=test_foo2, test_id_format="function")
    assert len(dct) == 1
    name = "test_foo2[foo]" if not pytest2 else "test_foo2[foo[0]-foo[1]]"
    i_param = dct[name]["pytest_params"]["i"]
    assert not isinstance(i_param, int)
    assert str(i_param) == "foo[0]"
    j_param = dct[name]["pytest_params"]["j"]
    assert not isinstance(j_param, int)
    assert str(j_param) == "foo[1]"

    # final test on automatic fixture: should be the same
    assert module_results_df.dtypes['a'].kind == 'O'
    assert module_results_df.dtypes['i'].kind == 'O'
    assert module_results_df.dtypes['j'].kind == 'O'

    # last note: nothing can be done for test_foo3
    # as soon as fixtures are created by @parametrize to handle fixture_ref, you cannot access the values anymore
    # TODO can this make it easier ? https://github.com/smarie/python-pytest-harvest/issues/44
    assert module_results_df.loc["test_foo3[a_is_foo]", "a_value"] == ['r', 1]
    assert module_results_df.loc["test_foo3[a_is_b]", "a_value"] == (1, 'hello')
