import torch
from torch import Tensor
from typing import Optional


def gelu(input: Tensor, approximate: str = "none") -> Tensor:
    """Applies the Gaussian Error Linear Unit function.

    The GELU activation is defined as:

    GELU(x) = x * Φ(x)

    where Φ(x) is the cumulative distribution function of the standard
    normal distribution.

    When approximate='tanh':
        GELU(x) ≈ 0.5 * x * (1 + tanh(√(2/π) * (x + 0.044715 * x³)))

    See torch.nn.GELU for more details.

    Arguments:
        input: the input tensor
        approximate: the approximation method. Can be 'none' or 'tanh'.
            Default: 'none'

    Returns:
        Tensor: the output tensor with same shape as input

    Example:
        import torch
        import torch.nn.functional as F
        x = torch.tensor([-1.0, 0.0, 1.0])
        F.gelu(x)
    """
    if approximate == "tanh":
        return torch.nn.functional.gelu(input, approximate="tanh")
    return torch.nn.functional.gelu(input)


def silu(input: Tensor, inplace: bool = False) -> Tensor:
    """Sigmoid Linear Unit activation function (also known as Swish).

    silu(x) = x * sigmoid(x) = x * (1 / (1 + exp(-x)))

    Parameters:
        input (Tensor): input tensor of shape (N, *)
        inplace (bool): if True, do the operation in-place. Default: False

    Returns:
        the activated tensor

    Example:
        >>> import torch
        >>> x = torch.zeros(3)
        >>> torch.nn.functional.silu(x)
        tensor([0., 0., 0.])
    """
    if inplace:
        return input.mul_(torch.sigmoid(input))
    return input * torch.sigmoid(input)


def mish(input: Tensor, inplace: bool = False) -> Tensor:
    """Applies the Mish activation function element-wise.

    Mish is a smooth, non-monotonic function:
    mish(x) = x * tanh(softplus(x)) = x * tanh(ln(1 + exp(x)))

    Args:
        input: input tensor
        inplace: if True, perform in-place. Default is False

    Returns:
        Tensor with same shape as input

    Examples:
        >>> import torch
        >>> x = torch.ones(5)
        >>> torch.nn.functional.mish(x)
    """
    if inplace:
        return input.mul_(torch.tanh(torch.nn.functional.softplus(input)))
    return input * torch.tanh(torch.nn.functional.softplus(input))
