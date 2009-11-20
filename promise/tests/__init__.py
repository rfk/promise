
import os
import timeit
import unittest

class TestPromise(unittest.TestCase):

    def _timeit(self,modnm,funcnms,funcnm):
        setup = "from promise.tests.%s import verify, %s" % (modnm,funcnms)
        t = timeit.Timer("verify(%s)" % (funcnm,),setup)
        print funcnm, min(t.repeat(number=100000))
        return min(t.repeat(number=100000))

    def _make_test(modnm):
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

