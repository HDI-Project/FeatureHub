from os.path import abspath, realpath, dirname, join
import sys
sys.path.insert(0, join(dirname(abspath(realpath(__file__))),'..','..'))

import featurefactory.util

# ------------------------------------------------------------------------------ 
# Test get_source

def test_get_source():
    def f():
        return 0

    def g(a):
        return a+f()

    def h(a,b,c,d):
        import os
        import sys
        os.getcwd()
        g(1)
        c+d

    # should throw no errors
    code_f = featurefactory.util.get_source(f)
    code_g = featurefactory.util.get_source(g)
    code_h = featurefactory.util.get_source(h)

# ------------------------------------------------------------------------------ 
# Test get_function()

def test_get_function():
    def f():
        return 0

    def g(a):
        return a + f()

    def h(a,b,c):
        x = g(a) + b + c

    def w(h,g):
        return h+g()

    def x():
        pass

    def y(a):
        if a:
            y(not a)

    def z(a,b,c):
        import pandas
        import numpy
        return pandas.DataFrame(numpy.random.randn(a,b)) * h(a,b,c)

    for fn in [f, g, h, w, x, y, z]:
        code = featurefactory.util.get_source(fn)
        function = featurefactory.util.get_function(code)

# ------------------------------------------------------------------------------ 
# Test run_isolated

# Must define f at global scope. See http://stackoverflow.com/q/3288595/2514228
def f(a):
    return a+1

def test_run_isolated():
    args = [1,3,7]
    for arg in args:
        assert f(arg) == featurefactory.util.run_isolated(f, arg)

# ------------------------------------------------------------------------------ 
# Test compute_dataset_hash

def test_compute_dataset_hash():
    def create_dummy_dataset(n=5, m=10):
        import pandas as pd
        import numpy as np
        return [pd.DataFrame(np.random.randn(m,m)) for i in range(n)]

    # create dummy
    dataset = create_dummy_dataset()
    dataset_hash = featurefactory.util.compute_dataset_hash(dataset)

    # should get the same hash if we recompute with no changes
    assert dataset_hash == featurefactory.util.compute_dataset_hash(dataset)

    # change the data, recompute, should get different hash
    dataset[0].iloc[0,0] += 1
    assert dataset_hash != featurefactory.util.compute_dataset_hash(dataset)
