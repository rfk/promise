"""

  promise:  bytecode optimisations based on staticness assertions.

"""

import types

from promise.byteplay import *


class BrokenPromiseError(Exception):
    """Exception raised when you make a promise that is provably broken."""
    pass


def _ids():
    """Generator producing unique ids."""
    i = 0
    while True:
        i += 1
        yield i 
_ids = _ids()


def new_name(name=None):
    """Generate a new unique variable name

    If the given name is not None, it is included in the generated name for
    each of reference in e.g. tracebacks or bytecode inspection.
    """
    if name is None:
        return "_promise_var%s" % (_ids.next(),)
    else:
        return "_promise_var%s_%s" % (_ids.next(),name,)


def apply_deferred_promises(func):
    """Apply any deferred promises attached to a function."""
    try:
        deferred = func._deferred_promises
    except AttributeError:
        pass
    else:
        del func._deferred_promises
        #  Remove the bootstrapping code inserted by defer()
        c = Code.from_code(func.func_code)
        idx = c.code.index((POP_TOP,None))
        del c.code[:idx+1]
        #  Apply each promise in turn
        for p in deferred:
            p.apply(func,c)
        #  Use the transformed bytecode in subsequent calls to func
        func.func_code = c.to_code()
    pass


class Promise(object):
    """Base class for promises.

    A "Promise" represents a transformation that can be applied to a function's
    bytecode, given that the user promises to only use the function in certain
    restricted ways.
    """

    def __init__(self):
        pass

    def __call__(self,*args):
        """Apply this promise with a function, module, dict, etc.

        Calling a promise arranges for it to be applied to any functions
        found in the given arguments.  Each argument can be a raw function,
        or a class, module or iterable of functions.
        """
        if not args:
            return None
        for arg in args:
            if isinstance(arg,types.FunctionType):
                self.decorate(arg)
            else:
                try:
                    subargs = iter(arg)
                except TypeError:
                    subargs =  (getattr(arg,nm) for nm in dir(arg))
                for subarg in subargs:
                    if isinstance(subarg,types.FunctionType):
                        self(subarg)
        return args[0]

    def decorate(self,func):
        """Decorate the given function to apply this promise.

        This can either directly apply the promise, or defer its application
        until the function is first executed.  The return value is ignored;
        in practise this means that decorate() must modify the given function
        rather than consruct a wrapper as a standard decorator might do.
        """
        pass

    def apply(self,func,code):
        """Apply this promise to the given function.

        The argument 'func' is the function to which the promise is being
        applied, and 'code' is a byteplay code object representing its code.
        The code object should be modified in-place.
        """
        pass

    def defer(self,func):
        """Defer the application of this promise func is first executed."""
        try:
            deferred = func._deferred_promises
        except AttributeError:
            deferred = []
            func._deferred_promises = deferred
            #  Add code to apply the promise when func is first executed.
            #  These opcodes are removed by apply_deferred_promises()
            c = Code.from_code(func.func_code)
            c.code.insert(0,(LOAD_CONST,apply_deferred_promises))
            c.code.insert(1,(LOAD_CONST,func))
            c.code.insert(2,(CALL_FUNCTION,1))
            c.code.insert(3,(POP_TOP,None))
            func.func_code = c.to_code()
        deferred.append(self)

    def apply_or_defer(self,func):
        """Apply this promise, or defer it is others are already deferred.

        It's generally a good idea to use this instead of directly applying
        a promise, since it ensured multiple promises will be applied in the
        order in which they appear in code.
        """
        try:
            deferred = func._deferred_promises
        except AttributeError:
            code = Code.from_code(func.func_code)
            self.apply(func,code)
            func.func_code = code.to_code()
        else:
            deferred.append(self)


class invariant(Promise):
    """Promise that the given names are invariant during the function call.

    This promise allows the names to be loaded once, at the beginning of the
    function, and accessed through local variables from there on out.
    """

    def __init__(self,names):
        self.names = names
        super(invariant,self).__init__()

    def decorate(self,func):
        self.apply_or_defer(func)

    def apply(self,func,code):
        local_names = {}
        load_ops = []
        for (i,(op,arg)) in enumerate(code.code):
            #  Replace any LOADs of invariant names with a LOAD_FAST
            if op in (LOAD_GLOBAL,LOAD_NAME,LOAD_DEREF):
                if arg in self.names:
                    if arg not in local_names:
                        local_names[arg] = new_name(arg)
                        load_ops.append((op,arg))
                        load_ops.append((STORE_FAST,local_names[arg]))
                    code.code[i] = (LOAD_FAST,local_names[arg])
            #  Quick check that invariant names arent munged
            elif op in (STORE_NAME,STORE_GLOBAL,STORE_FAST,STORE_DEREF):
                if arg in self.names:
                    msg = "name '%s' was promised invariant, but assigned to"
                    raise BrokenPromiseError(msg % (arg,))
            elif op in (DELETE_NAME,DELETE_GLOBAL,DELETE_FAST):
                if arg in self.names:
                    msg = "name '%s' was promised invariant, but deleted"
                    raise BrokenPromiseError(msg % (arg,))
        #  Insert code to load the names in local vars at start of function
        for i,op in enumerate(load_ops):
            code.code.insert(i,op)


class constant(Promise):
    """Promise that the given names are constant

    This promise allows the objects referred to by the names to be stored
    directly in the code as constants, eliminating name lookups.
    """

    def __init__(self,names):
        self.names = names
        super(constant,self).__init__()

    def decorate(self,func):
        #  Delay constant lookup until runtime.
        #  This lets us forward-declare constants such as other module funcs.
        self.defer(func)

    def _load_name(self,func,nm,op=None):
        """Look up the given name in the scope of the given function.

        This is an attempt to replicate the name lookup rules of LOAD_NAME,
        LOAD_GLOBAL and friends.  If a specific bytecode op is specified,
        only the rules for that operation are applied.

        If the name cannot be found, NameError is raised.
        """
        # TODO: loading of local or closed-over names.
        try:
            try:
                return func.func_globals[nm]
            except KeyError:
                return func.func_globals["__builtins__"][nm]
        except KeyError:
            raise NameError(nm)

    def apply(self,func,code):
        constant_map = {}
        constants = []
        for (i,(op,arg)) in enumerate(code.code):
            #  Replace LOADs of matching names with LOAD_CONST
            if op in (LOAD_GLOBAL,):
                if arg in self.names:
                    try:
                        val = constant_map[arg]
                    except KeyError:
                        val = self._load_name(func,arg,op)
                        constant_map[arg] = val
                        constants.append(val)
                    code.code[i] = (LOAD_CONST,val)
            elif op in (LOAD_NAME,LOAD_DEREF,LOAD_FAST):
                if arg in self.names:
                    raise TypeError("sorry, only global constants are currently supported [%s]" % (arg,))
            #  Quick check that constant names arent munged
            elif op in (STORE_NAME,STORE_GLOBAL,STORE_FAST,STORE_DEREF):
                if arg in self.names:
                    msg = "name '%s' was promised constant, but assigned to"
                    raise BrokenPromiseError(msg % (arg,))
            elif op in (DELETE_NAME,DELETE_GLOBAL,DELETE_FAST):
                if arg in self.names:
                    msg = "name '%s' was promised constant, but deleted"
                    raise BrokenPromiseError(msg % (arg,))
            elif op == LOAD_CONST:
                if arg not in constants:
                    constants.append(arg)
        #  If any constants define a '_promise_fold_constant' method,
        #  let them have a crack at the bytecode as well.
        for const in constants:
            try:
                fold = const._promise_fold_constant
            except AttributeError:
                pass
            else:
                fold(func,code)


class can_inline(Promise):
    """Promise that a function can be inlined.

    This involves a bodily insertion of the bytecode of the function in
    place of its use as a constant.
    """

    def decorate(self,func):
        c = Code.from_code(func.func_code)
        if c.varargs:
            raise TypeError("can't currently inline functions with varargs")
        if c.varkwargs:
            raise TypeError("can't currently inline functions with varkwargs")
        func._promise_fold_constant = self._make_fold_method(func)

    def _make_fold_method(self,source_func):
        def fold(dest_func,dest_code):
            toinline = self._find_inlinable_call(source_func,dest_code)
            while toinline is not None:
                (loadsite,callsite) = toinline
                source_code = Code.from_code(source_func.func_code)
                #  Remove any setlineno ops from the source bytecode
                new_code = [c for c in source_code.code if c[0] != SetLineno]
                source_code.code[:] = new_code
                #  Munge the source bytecode to leave return value on stack
                end = Label()
                source_code.code.append((end,None))
                for (i,(op,arg)) in enumerate(source_code.code):
                    if op == RETURN_VALUE:
                        source_code.code[i] = (JUMP_ABSOLUTE,end)
                #  Munge the source bytecode to directly pop args from stack
                # TODO: support keyword arguments
                name_map = self._rename_local_vars(source_code)
                numargs = dest_code.code[callsite][1]
                for i in xrange(numargs):
                    argname = source_func.func_code.co_varnames[i]
                    source_code.code.insert(0,(STORE_FAST,name_map[argname]))
                #  Replace the call with the munged code
                dest_code.code[callsite:callsite+1] = source_code.code
                del dest_code.code[loadsite]
                #  Rinse and repeat
                toinline = self._find_inlinable_call(source_func,dest_code)
        return fold

    def _find_inlinable_call(self,func,code):
        """Find an inlinable call to func in the given code.

        If such a call is found, a tuple (loadsite,callsite) is returned
        giving the position of the LOAD_CONST on the function and the matching
        CALL_FUNCTION.  If no inlinable call is found, returns None.
        """
        # TODO: this is wrong in so many ways...
        for (i,(op,arg)) in enumerate(code.code):
            if op == LOAD_CONST and arg == func:
                loadsite = callsite = i
                # TODO: use stack effects to ensure it's calling this func
                while callsite < len(code.code) and code.code[callsite][0] != CALL_FUNCTION:
                    callsite += 1
                if callsite != len(code.code):
                    (op,arg) = code.code[callsite]
                    #  Check that it doesn't use kwdargs
                    if arg == (arg & 0xFF):
                        return (loadsite,callsite)
        return None

    def _rename_local_vars(self,code):
        """Rename the local variables in the given code to new unique names.

        Returns a dictionary mapping old names to new names.
        """
        name_map = {}
        for (i,(op,arg)) in enumerate(code.code):
            if op in (LOAD_FAST,STORE_FAST,DELETE_FAST):
                try:
                    newarg = name_map[arg]
                except KeyError:
                    newarg = new_name(arg)
                    name_map[arg] = newarg
                code.code[i] = (op,newarg)
        return name_map


class sensible(Promise):
    """Promise that a function is sensibly behaved.  Basically:

        * all builtins are constant
        * all global functions are constant
        * all other globals are invariant

    """

    def decorate(self,func):
        self.defer(func)

    def apply(self,func,code):
        callable_globals = set()
        other_globals = set()
        for (nm,obj) in func.func_globals.iteritems():
            if callable(obj):
                callable_globals.add(nm)
            else:
                other_globals.add(nm)
        constant(__builtins__).apply(func,code)
        constant(callable_globals).apply(func,code)
        invariant(other_globals).apply(func,code)
 
