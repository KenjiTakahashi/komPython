# -*- coding: utf-8 -*-


from z1 import p
from z2 import pHit, pMiss
from z4 import norm


world = ['green', "red", "red", 'green', 'green']


def sense(p, Z):
    return norm([pp * (w == Z and pHit or pMiss) for pp, w in zip(p, world)])


print(sense(p, "red"))
print(sense(p, 'green'))
