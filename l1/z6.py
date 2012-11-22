# -*- coding: utf-8 -*-


from z1 import p
from z5 import sense


def sense2(p, measurements):
    for m in measurements:
        p = sense(p, m)
    return p


print(sense2(p, ["red", 'green']))
