import sys
from itertools import chain

from decorator import FunctionMaker
from inspect import isgeneratorfunction

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature

try:
    from decorator import iscoroutinefunction
except ImportError:
    try:
        from inspect import iscoroutinefunction
    except ImportError:
        # let's assume there are no coroutine functions in old Python
        def iscoroutinefunction(f):
            return False


class MyFunctionMaker(FunctionMaker):
    """
    Overrides FunctionMaker so that additional arguments can be inserted in the resulting signature.
    """

    @classmethod
    def create(cls, obj, body, evaldict, defaults=None,
               doc=None, module=None, addsource=True, add_args=None, **attrs):
        """
        Create a function from the strings name, signature and body.
        evaldict is the evaluation dictionary. If addsource is true an
        attribute __source__ is added to the result. The attributes attrs
        are added, if any.
        """
        if isinstance(obj, str):  # "name(signature)"
            name, rest = obj.strip().split('(', 1)
            signature = rest[:-1]  # strip a right parens
            func = None
        else:  # a function
            name = None
            signature = None
            func = obj
        self = cls(func, name, signature, defaults, doc, module)
        ibody = '\n'.join('    ' + line for line in body.splitlines())
        caller = evaldict.get('_call_')  # when called from `decorate`
        if caller and iscoroutinefunction(caller):
            body = ('async def %(name)s(%(signature)s):\n' + ibody).replace(
                'return', 'return await')
        else:
            body = 'def %(name)s(%(signature)s):\n' + ibody

        # --- HACK part 1 -----
        if add_args is not None:
            for arg in add_args:
                if arg not in self.args:
                    self.args = [arg] + self.args
                else:
                    # the argument already exists in the wrapped function, no problem.
                    pass

            # update signatures (this is a copy of the init code)
            allargs = list(self.args)
            allshortargs = list(self.args)
            if self.varargs:
                allargs.append('*' + self.varargs)
                allshortargs.append('*' + self.varargs)
            elif self.kwonlyargs:
                allargs.append('*')  # single star syntax
            for a in self.kwonlyargs:
                allargs.append('%s=None' % a)
                allshortargs.append('%s=%s' % (a, a))
            if self.varkw:
                allargs.append('**' + self.varkw)
                allshortargs.append('**' + self.varkw)
            self.signature = ', '.join(allargs)
            self.shortsignature = ', '.join(allshortargs)
        # ---------------------------

        func = self.make(body, evaldict, addsource, **attrs)

        # ----- HACK part 2
        if add_args is not None:
            # delete this annotation otherwise the inspect.signature method relies on the wrapped object's signature
            del func.__wrapped__

        return func


def _extract_additional_args(f_sig, add_args_names, args, kwargs):
    """
    Processes the arguments received by our caller so that at the end, args
    and kwargs only contain what is needed by f (according to f_sig). All
    additional arguments are returned separately, in order described by
    `add_args_names`. If some names in `add_args_names` are present in `f_sig`,
    then the arguments will appear both in the additional arguments and in
    *args, **kwargs.

    In the end, only *args can possibly be modified by the procedure (by removing
    from it all additional arguments that were not in f_sig and were prepended).

    So the result is a tuple (add_args, args)

    :return: a tuple (add_args, args) where `add_args` are the values of
        arguments named in `add_args_names` in the same order ; and `args` is
        the positional arguments to send to the wrapped function together with
        kwargs (args now only contains the positional args that are required by
        f, without the extra ones)
    """
    # -- first the 'truly' additional ones (the ones not in the signature)
    add_args = [None] * len(add_args_names)
    for i, arg_name in enumerate(add_args_names):
        if arg_name not in f_sig.parameters:
            # remove this argument from the args and put it in the right place
            add_args[i] = args[0]
            args = args[1:]

    # -- then the ones that already exist in the signature. Thanks,inspect pkg!
    bound = f_sig.bind(*args, **kwargs)
    for i, arg_name in enumerate(add_args_names):
        if arg_name in f_sig.parameters:
            add_args[i] = bound.arguments[arg_name]

    return add_args, args


def _wrap_caller_for_additional_args(func, caller, additional_args):
    """
    This internal function wraps the caller so as to handle all cases
    (if some additional args are already present in the signature or not)
    so as to ensure a consistent caller signature.

    :return: a new caller wrapping the caller, to be used in `decorate`
    """
    f_sig = signature(func)

    # We will create a caller above the original caller in order to check
    # if additional_args are already present in the signature or not, and
    # act accordingly
    original_caller = caller

    # -- then create the appropriate function signature according to
    # wrapped function signature assume that original_caller has all
    # additional args as first positional arguments, in order
    if not isgeneratorfunction(original_caller):
        def caller(f, *args, **kwargs):
            # Retrieve the values for additional args.
            add_args, args = _extract_additional_args(f_sig, additional_args,
                                                      args, kwargs)

            # Call the original caller
            return original_caller(f, *chain(add_args, args),
                                   **kwargs)
    else:
        def caller(f, *args, **kwargs):
            # Retrieve the value for additional args.
            add_args, args = _extract_additional_args(f_sig, additional_args,
                                                      args, kwargs)

            # Call the original caller
            for res in original_caller(f, *chain(add_args, args),
                                       **kwargs):
                yield res

    return caller


def my_decorate(func, caller, extras=(), additional_args=()):
    """
    A clone of 'decorate' with the possibility to add additional args to the function signature,
    and with support for generator functions.
    """
    if len(additional_args) > 0:
        caller = _wrap_caller_for_additional_args(func, caller, additional_args)

    evaldict = dict(_call_=caller, _func_=func)
    es = ''
    for i, extra in enumerate(extras):
        ex = '_e%d_' % i
        evaldict[ex] = extra
        es += ex + ', '

    if not ('3.5' <= sys.version < '3.6'):
        create_generator = isgeneratorfunction(caller)
    else:
        # With Python 3.5: apparently isgeneratorfunction returns
        # True for all coroutines

        # However we know that it is NOT possible to have a generator
        # coroutine in python 3.5: PEP525 was not there yet.
        create_generator = isgeneratorfunction(caller) and not iscoroutinefunction(caller)

    if create_generator:
        fun = MyFunctionMaker.create(
            func, "for res in _call_(_func_, %s%%(shortsignature)s):\n"
                  "    yield res" % es,
            evaldict, add_args=reversed(additional_args or ()), __wrapped__=func)
    else:
        fun = MyFunctionMaker.create(
            func, "return _call_(_func_, %s%%(shortsignature)s)" % es,
            evaldict, add_args=reversed(additional_args), __wrapped__=func)
    if hasattr(func, '__qualname__'):
        fun.__qualname__ = func.__qualname__
    return fun
