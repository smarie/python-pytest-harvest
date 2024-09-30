import pytest


@pytest.mark.parametrize("a", [0], ids=["a::0"])
def test_a(a):
    pass


def test_b():
    pass


class TestC:
    def test_c(self):
        pass

    @pytest.mark.parametrize("a", [0], ids=["a::0"])
    def test_d(self, a):
        pass


def test_synthesis(module_results_dct):
    assert list(module_results_dct) == [
        'test_a[a::0]',
        'test_b',
        'test_c',
        'test_d[a::0]'
    ]
