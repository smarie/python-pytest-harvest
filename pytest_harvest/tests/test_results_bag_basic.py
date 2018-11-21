from pytest_harvest import ResultsBag


def test_results_bag_basic():
    r = ResultsBag()

    r.foo = 1
    assert r['foo'] == 1
    assert r == {'foo': 1}
    assert dict(r) == {'foo': 1}
    assert str(r) == "ResultsBag:\n{'foo': 1}"

    del r.foo
    assert 'foo' not in r
    assert r == {}
    assert dict(r) == {}
    assert str(r) == "ResultsBag:\n{}"

    assert hash(r) == id(r)
