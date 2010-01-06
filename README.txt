

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
directly inlined into the bytecode to avoid the overhead of a function call:

    @promise.constant(("calculate",))
    def aggregate(pairs):
        #  calculate() is a pure constant, so it will be inlined here.
        return sum(calculate(a,b) for (a,b) in pairs)

The currently available promises are:

    * invariant(names):  promise that variables having the given names will
                         not change value during execution of the function.

    * constant(names):   promise that variables having the given names will
                         always refer to the same object, across all calls
                         to the function.

    * pure():   promise that the function is a transparent mapping from inputs
                to outputs; this opens up the possibility of inling it directly
                into other functions.

    * sensible():   promise that the function is "sensibly behaved".  All
                    builtins and module-level functions are considered
                    constant; all other module-level names are considered
                    invariant.

Promise is built on Noam Raphael's fantastic "byteplay" module; since the
official byteplay distribution doesn't support Python 2.6, a local version with
appropriate patches is included with promise.
