import torch
from torch._C import _add_docstr


# Low-rank matrix approximation via randomized SVD
randomized_svd = _add_docstr(
    torch._C._linalg.randomized_svd,
    """TODO: add docstring""",
)


# Truncated eigendecomposition for symmetric matrices
truncated_eigh = _add_docstr(
    torch._C._linalg.truncated_eigh,
    """TODO: add docstring""",
)


# Sparse Cholesky factorization
sparse_cholesky = _add_docstr(
    torch._C._linalg.sparse_cholesky,
    """TODO: add docstring""",
)
