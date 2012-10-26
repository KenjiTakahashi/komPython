# -*- coding: utf-8 -*-


from z3 import p


def n(p):
    return [pp / sum(p) for pp in p]


print(n(p))
