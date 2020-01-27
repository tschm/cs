import numpy as np


# compute the oscillator
def osc(prices, fast=32, slow=96, scaling=True):
    #f,g = 1 - 1/fast, 1-1/slow

    diff = prices.ewm(com=fast-1).mean() - prices.ewm(com=slow-1).mean()
    if scaling:
        s = diff.std()
    else:
        s = 1

    return diff/s


def returns_adjust(price, com=32, min_periods=300, clip=4.2):
    r = np.log(price).diff()
    return (r / r.ewm(com=com, min_periods=min_periods).std()).clip(-clip, +clip)


def shrink2id(matrix, lamb=1.0):
    return matrix * lamb + (1 - lamb) * np.eye(N=matrix.shape[0])
