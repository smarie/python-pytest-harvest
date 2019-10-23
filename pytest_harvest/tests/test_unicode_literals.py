from __future__ import unicode_literals  # python 2 strings are different from python 3 strings
from pytest_harvest.results_session import _get_filterset


def test_filterset():
    assert _get_filterset('toto') == {'toto'}
