# -*- coding: utf-8 -*-


p = [0, 0, 0, 1, 0]


def move(p, U):
    c = p[:]
    for _ in xrange(U):
        c.insert(0, c.pop())
    return c


assert move(p, 1) == [0, 0, 0, 0, 1]
assert move(p, 2) == [1, 0, 0, 0, 0]
