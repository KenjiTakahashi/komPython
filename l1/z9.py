# -*- coding: utf-8 -*-


from z8 import move2


p = [0, 1, 0, 0, 0]


for _ in xrange(1000):
    p = move2(p, 2)
    print(p)
