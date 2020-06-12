import numpy as np


def valid(a):
    """
    Construct the valid subset of a (correlation) matrix a
    :param a: n x n matrix

    :return: Tuple of a boolean vector indicating if row/column is valid and the valid subset of the matrix
    """
    # make sure a  is quadratic
    assert a.shape[0] == a.shape[1]
    v = np.isfinite(np.diag(a))
    return v, a[:, v][v]


# that's somewhat not needed...
def a_norm(vector, a=None):
    """
    Compute the a-norm of a vector
    :param vector: the n x 1 vector
    :param a: n x n matrix
    :return:
    """
    if a is None:
        return np.linalg.norm(vector[np.isfinite(vector)], 2)

    # make sure a is quadratic
    assert a.shape[0] == a.shape[1]
    # make sure the vector has the right number of entries
    assert vector.size == a.shape[0]

    v, mat = valid(a)

    if v.any():
        return np.sqrt(np.dot(vector[v], np.dot(mat, vector[v])))
    else:
        return np.nan


def inv_a_norm(vector, a=None):
    """
    Compute the a-norm of a vector
    :param vector: the n x 1 vector
    :param a: n x n matrix
    :return:
    """
    if a is None:
        return np.linalg.norm(vector[np.isfinite(vector)], 2)

    # make sure a is quadratic
    assert a.shape[0] == a.shape[1]
    # make sure the vector has the right number of entries
    assert vector.size == a.shape[0]

    v, mat = valid(a)

    if v.any():
        return np.sqrt(np.dot(vector[v], np.linalg.solve(mat, vector[v])))
    else:
        return np.nan


def solve(a, b):
    """
    Solve the linear system a*x = b
    Note that only the same subset of the rows and columns of a might be "warm"

    :param a: n x n matrix
    :param b: n x 1 vector

    :return: The solution vector x (which may contain NaNs
    """
    # make sure a is quadratic
    assert a.shape[0] == a.shape[1]
    # make sure the vector b has the right number of entries
    assert b.size == a.shape[0]

    x = np.nan * np.ones(b.size)
    v, mat = valid(a)

    if v.any():
        x[v] = np.linalg.solve(mat, b[v])

    return x
