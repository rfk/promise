
import promise


@promise.pure()
def calculate(a,b):
    return a*100 + b*10


def inline0(amax,bmax):
    return [calculate(a,b) for a in xrange(amax) for b in xrange(bmax)]


def verify(inline):
    res = inline(1,1)
    assert res == [0]
    res = inline(4,4)
    assert res == [0,10,20,30,100,110,120,130,200,210,220,230,300,310,320,330]


@promise.constant(["calculate"])
def inline1(amax,bmax):
    return [calculate(a,b) for a in xrange(amax) for b in xrange(bmax)]


@promise.constant(__builtins__)
@promise.constant(["calculate"])
def inline2(amax,bmax):
    return [calculate(a,b) for a in xrange(amax) for b in xrange(bmax)]


