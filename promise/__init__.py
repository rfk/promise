
from promise.byteplay import *
from functools import wraps

class _Placeholder:
    pass


def invariant(names):
    """Promise that the given names are invariant during the function call.

    This promise allows the names to be loaded once, at the beginning of the
    function, and accessed through local variables from there on out.
    """
    def decorator(func):
        c = Code.from_code(func.func_code)
        found = set()
        load_ops = []
        for (i,(op,arg)) in enumerate(c.code):
            if op in (LOAD_GLOBAL,LOAD_NAME,LOAD_DEREF):
                if arg in names:
                    nm = "__promise_" + arg
                    c.code[i] = (LOAD_FAST,nm)
                    if arg not in found:
                        load_ops.append((op,arg))
                        load_ops.append((STORE_FAST,nm))
                        found.add(arg)
        for i,op in enumerate(load_ops):
            c.code.insert(i,op)
        func.func_code = c.to_code()
        return func
    return decorator


def constant(names):
    """Promise that the given names are constant across every call.

    This promise allows the objects to be directly attached to the function
    as constants, avoiding name lookups.  It may also enable some other
    optimizations (e.g. inlined functions).
    """
    def decorator(func):
        c = Code.from_code(func.func_code)
        found = set()
        load_ops = []
        for (i,(op,arg)) in enumerate(c.code):
            if op in (LOAD_GLOBAL,LOAD_NAME,LOAD_DEREF):
                if arg in names:
                    nm = "__promise_" + arg
                    c.code[i] = (LOAD_FAST,nm)
                    if arg not in found:
                        load_ops.append((op,arg))
                        load_ops.append((STORE_FAST,nm))
                        found.add(arg)
        for i,op in enumerate(load_ops):
            c.code.insert(i,op)
        func.func_code = c.to_code()
        return func
    return decorator
