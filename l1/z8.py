# -*- coding: utf-8 -*-


Pe = 0.8
Pu = 0.1


def move2(p, U):
    return [
        p[i - 1] * Pu + p[i - 2] * Pe + p[i - 3] * Pu for i in xrange(len(p))
    ]


assert move2([0, 1, 0, 0, 0], 2) == [0, 0, 0.1, 0.8, 0.1]
assert move2([0, 0.5, 0, 0.5, 0], 2) == [0.4, 0.05, 0.05, 0.4, 0.1]
