
import os
import timeit
import unittest

import promise


class TestPromise(unittest.TestCase):
    """Run timing tests for suitable sub-modules.

    This class finds all sub-modules of promise.tests and tries to load each
    of them as a timing test.  A module named 'testmod' must define a function
    'verify' and a series of functions 'testmod0', 'testmod1' etc.  The verify
    function will be called with each of the testmodX functions in order, and
    we assert that each is successively faster than its predecessor.
    """

    def _timeit(self,modnm,funcnms,funcnm):
        setup = "from promise.tests.%s import verify, %s" % (modnm,funcnms)
        ts = timeit.Timer("verify(%s)"%(funcnm,),setup).repeat(number=100000)
        print funcnm, sorted(ts)
        return min(ts)

    def _make_test(modnm):
        """Make a timing test method from the given module name."""
        def test(self):
            mod = getattr(__import__("promise.tests."+modnm).tests,modnm)
            funcs = []
            for funcnm in dir(mod):
                if funcnm.startswith(modnm):
                   funcs.append(funcnm)
            funcs.sort()
            funcnms = ",".join(funcs)
            t0 = self._timeit(modnm,funcnms,funcs[0])
            for funcnm in funcs[1:]:
                t1 = self._timeit(modnm,funcnms,funcnm)
                self.assertTrue(t0 > t1)
                t0 = t1
        test.__name__ = "test_" + modnm
        return test

    for modnm in os.listdir(os.path.dirname(__file__)):
        if modnm.endswith(".py") and modnm != "__init__.py":
            nm = modnm[:-3]
            locals()["test_"+nm] = _make_test(nm)



def test_README():
    """Ensure that the README is in sync with the docstring.

    This test should always pass; if the README is out of sync it just updates
    it with the contents of promise.__doc__.
    """
    dirname = os.path.dirname
    readme = os.path.join(dirname(dirname(dirname(__file__))),"README.txt")
    if not os.path.isfile(readme):
        f = open(readme,"wb")
        f.write(promise.__doc__)
        f.close()
    else:
        f = open(readme,"rb")
        if f.read() != promise.__doc__:
            f.close()
            f = open(readme,"wb")
            f.write(promise.__doc__)
            f.close()

