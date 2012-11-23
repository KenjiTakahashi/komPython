# -*- coding: utf-8 -*-


from z1 import p
from z5 import sense
from z8 import move2


motions = [1, 1]
measurements = ["red", 'green']


for measur, motion in zip(measurements, motions):
    p = move2(sense(p, measur), motion)
print(p)
