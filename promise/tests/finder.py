
import promise

items = range(100)

def finder0(item):
    i = 0
    while i < len(items):
        if items[i] == item:
            return True
        i += 1
    return False

def verify(finder):
    assert finder(0)
    assert finder(42)
    assert not finder(101)
    assert not finder(1001)

@promise.invariant(["len"])
def finder1(item):
    i = 0
    while i < len(items):
        if items[i] == item:
            return True
        i += 1
    return False

@promise.invariant(["items","len",])
def finder2(item):
    i = 0
    while i < len(items):
        if items[i] == item:
            return True
        i += 1
    return False

#@promise.constant(["len"])
#@promise.invariant(["items"])
@promise.sensible()
def finder3(item):
    i = 0
    while i < len(items):
        if items[i] == item:
            return True
        i += 1
    return False

