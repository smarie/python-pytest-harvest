# META
# {'passed': 2, 'failed': 0}
# END META

import pytest


@pytest.mark.parametrize('p', ['hello', 'world'], ids=str)
def test_foo(p):
    print(p)
