# -*- coding: utf-8 -*-


import unittest
import sys
from cStringIO import StringIO


class Test1(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, StringIO()
        self.a = .2 * .2

    def tearDown(self):
        sys.stdout = self.held

    def test_z1(self):
        import z1
        self.assertEqual(sys.stdout.getvalue(), "[0.2, 0.2, 0.2, 0.2, 0.2]\n")

    def test_z2(self):
        import z2
        self.assertEqual(
            sys.stdout.getvalue(),
            "{0}\n".format([self.a, .12, .12, self.a, self.a])
        )

    def test_z3(self):
        import z3
        self.assertEqual(sys.stdout.getvalue(), "0.36\n")

    def test_z4(self):
        import z4
        from z3 import s
        b = self.a / s
        c = .12 / s
        self.assertEqual(
            sys.stdout.getvalue(),
            "{0}\n".format([b, c, c, b, b])
        )

    def test_z5(self):
        import z5
        from z3 import s
        output = sys.stdout.getvalue().split('\n')
        b = self.a / s
        c = .12 / s
        self.assertEqual(
            "{0}\n".format(output[0]), "{0}\n".format([b, c, c, b, b])
        )
        s = self.a * 2 + .12 * 3
        b = .12 / s
        c = self.a / s
        self.assertEqual(output[1], str([b, c, c, b, b]))

    def test_z6(self):
        pass

    def test_z7(self):
        import z7
        self.assertEqual(z7.move([0, 0, 0, 1, 0], 1), [0, 0, 0, 0, 1])

    def test_z8(self):
        import z8
        self.assertEqual(z8.move([0, 1, 0, 0, 0], 2), [0, 0, .1, .8, .1])
        self.assertEqual(z8.move([0, .5, 0, .5, 0], 2), [.4, .05, .05, .4, .1])


suite = unittest.TestLoader().loadTestsFromTestCase(Test1)
unittest.TextTestRunner(verbosity=1).run(suite)
