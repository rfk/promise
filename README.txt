

  promise:  bytecode optimisation using staticness assertions.

This is a module for applying some simple optimisations to function bytecode.
By promising that a function doesn't do certain things at run-time, it's
possible to apply optimisations that are not legal in the general case.

As a simple example, it's possible to promise that a function doesn't modify
(or care if anyone else modifies) any builtin functions by decorating it thus:

    @promise.constant(__builtins__)
    def function():
        ...

Such a promise will allow the builtins to be stored as direct object references
in the function bytecode, avoiding name lookups during function execution.

As another example, it's possible to promise that a function is pure; i.e. that
it's a simple algorithm for mapping input values to an output value:

    @promise.pure()
    def calculate(a,b):
        return 2*a*a + 3*b + 7

If a pure function is then used by another function as a constant, it can be
directly inlined into the bytecode to avoid the overhead of a function call.

Promise is built on Noam Raphael's fantastic "byteplay" module; since the
official byteplay distribution doesn't support Python 2.6, a local version with
appropriate patches is included with promise.
