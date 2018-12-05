# META
# {'passed': 4, 'skipped': 0, 'failed': 0}
# END META

from inspect import isgeneratorfunction

# from decorator import decorate
from pytest_harvest.decorator_hack import my_decorate


# A my_normal function
def my_normal():
    for i in range(10):
        print(i)
    return


assert not isgeneratorfunction(my_normal)
my_normal()


# A generator
def my_generator():
    for i in range(10):
        print(i)
        yield i


assert isgeneratorfunction(my_generator)
next(my_generator())


def test_normal_normal():
    # A my_normal wrapper around a normal function
    def normal_around_normal(f, *args, **kwargs):
        return my_normal()

    decorated = my_decorate(my_generator, normal_around_normal)
    assert not isgeneratorfunction(decorated)
    decorated()


def test_normal_gen():
    # A my_normal wrapper around a generator function
    def normal_around_gen(f, *args, **kwargs):
        for res in my_generator():
            # do not yield !
            pass
        return 15

    decorated = my_decorate(my_generator, normal_around_gen)
    assert not isgeneratorfunction(decorated)
    decorated()


def test_gen_gen():
    # A generator wrapper around a generator function
    def gen_around_gen(f, *args, **kwargs):
        for res in my_generator():
            yield res

    decorated = my_decorate(my_generator, gen_around_gen)
    assert isgeneratorfunction(decorated)
    next(decorated())


def test_gen_normal():
    # A generator wrapper around a my_normal function
    def gen_around_normal(f, *args, **kwargs):
        yield my_normal()

    decorated = my_decorate(my_normal, gen_around_normal)
    assert isgeneratorfunction(decorated)
    next(decorated())
