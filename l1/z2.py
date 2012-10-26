# -*- coding: utf-8 -*-


from z1 import p


pHit = .6
pMiss = .2


p = [i in [1, 2] and pp * pHit or pp * pMiss for i, pp in enumerate(p)]


print(p)
