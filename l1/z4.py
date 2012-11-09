# -*- coding: utf-8 -*-


from z3 import p


def norm(p):
    return [pp / sum(p) for pp in p]


print(norm(p))
