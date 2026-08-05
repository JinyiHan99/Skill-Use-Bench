---
name: pytorch-docstring
description: 'Skill for writing and editing docstrings in a PyTorch-style codebase. Use when asked to add, update, or review function/method documentation, especially for tensor operations, neural network modules, and mathematical functions. Follows the conventions established in torch/_tensor_docs.py and torch/nn/functional.py.'
---

# PyTorch Docstring Writing Guide

This skill covers the conventions for writing function and method docstrings in a PyTorch-style project. All docstrings must follow the Sphinx/reStructuredText (reST) format established by the project's existing documentation. When this skill is active, docstrings must be written using the patterns below — do not use Google-style, NumPy-style, or plain-text docstrings even if they seem more readable for simple functions.

## When to Use This Skill

- Adding docstrings to new public functions, methods, or classes
- Updating existing docstrings after API changes
- Documenting tensor operations with shape information
- Writing docstrings for neural network modules (forward methods, __init__)
- Adding mathematical formulations to algorithm documentation
- Reviewing docstring completeness and format compliance

## Prerequisites

- Sphinx documentation toolchain configured
- Project uses reStructuredText format for all docstrings
- LaTeX math rendering enabled in Sphinx config (`mathjax` or `imgmath`)

## Docstring Structure

Every public function docstring follows this exact section ordering. Sections that don't apply may be omitted, but the relative order of present sections must be preserved:

1. Function signature (first line, immediately after opening quotes)
2. Brief description (one sentence, separated by blank line)
3. Extended description (optional, for complex behavior)
4. Math formula (using `.. math::` directive)
5. Cross-references to related functions
6. Notes/Warnings (`.. note::`, `.. warning::`)
7. Args section
8. Keyword Args section (if applicable)
9. Returns section
10. Examples section

Omitting sections is acceptable, but reordering is not. For instance, placing `Examples` before `Args` or `Returns` before the math formula will cause documentation build inconsistencies.

## Raw String Requirement

All docstrings must use raw string literals (`r"""..."""`) to prevent backslash interpretation issues with LaTeX math notation. This applies even to docstrings that don't currently contain math — future edits may add formulas, and retrofitting `r` prefixes across hundreds of docstrings is error-prone:

```python
# Correct
def relu(input: Tensor, inplace: bool = False) -> Tensor:
    r"""Applies the rectified linear unit function element-wise.

    .. math::
        \text{ReLU}(x) = \max(0, x)
    """

# Incorrect — will break if math is added later
def relu(input: Tensor, inplace: bool = False) -> Tensor:
    """Applies the rectified linear unit function element-wise."""
```

## Args Section Format

Parameters are documented with a specific indentation and type annotation pattern. Each parameter entry uses exactly 4-space indentation under the `Args:` header, with the type in parentheses immediately after the parameter name:

```python
Args:
    input (Tensor): the input tensor of shape :math:`(N, C, H, W)`
    kernel_size (int or tuple): size of the pooling region. Can be a single
        number or a tuple `(kH, kW)`. Continuation lines use 8-space indent.
    stride (int or tuple, optional): stride of the pooling operation.
        Default: ``None`` (same as kernel_size)
    padding (int or tuple): implicit zero padding. Default: 0
```

Note the format rules:
- Type annotation always in parentheses: `(Tensor)`, `(int or tuple)`, `(bool, optional)`
- Optional parameters must include "optional" in the type and document their default value
- Default values use double backtick format: ``Default: ``None`` ``
- Multi-line descriptions use 8-space continuation indent (not 4)
- The word "Default" is always capitalized, followed by colon and space

## Tensor Shape Documentation

Tensor shapes must use the `:math:` inline directive with `\text{}` for dimension names. Do not use plain text or code formatting for shapes:

```python
# Correct
r"""
Args:
    input (Tensor): input tensor of shape :math:`(\text{minibatch}, \text{in\_channels}, iH, iW)`
    weight (Tensor): filters of shape :math:`(\text{out\_channels}, \frac{\text{in\_channels}}{\text{groups}}, kH, kW)`
"""

# Incorrect — plain text shapes
"""
Args:
    input (Tensor): input tensor of shape (minibatch, in_channels, iH, iW)
"""
```

Use `\text{}` for named dimensions (minibatch, channels, etc.) and plain math variables for positional dimensions (N, C, H, W). Underscores in dimension names must be escaped: `\text{in\_channels}`.

## Cross-References

Use Sphinx roles for all references to other documented symbols. Never use plain text or markdown-style links:

| Symbol Type | Sphinx Role | Example |
|------------|-------------|---------|
| Function | `:func:` | `:func:`torch.nn.functional.relu`` |
| Class | `:class:` | `:class:`~torch.nn.Module`` |
| Method | `:meth:` | `:meth:`~Tensor.view`` |
| Attribute | `:attr:` | `:attr:`torch.Tensor.grad`` |

The tilde prefix (`~`) strips the module path in rendered output — `:class:`~torch.nn.Module`` renders as just "Module". Use tilde for readability when the context makes the full path obvious; use the full path when disambiguation is needed.

## Examples Section

The Examples section uses a specific format with double-colon header and `>>>` prompts. Every public function must include at least one working example that demonstrates basic usage:

```python
r"""
Examples::

    >>> import torch
    >>> import torch.nn.functional as F
    >>> input = torch.randn(1, 3, 5, 5)
    >>> output = F.avg_pool2d(input, kernel_size=3, padding=1)
    >>> output.shape
    torch.Size([1, 3, 5, 5])
"""
```

Format requirements for examples:
- Header is exactly `Examples::` (capital E, double colon, no space before colons)
- One blank line between `Examples::` and the first `>>>` line
- Import statements must be included — do not assume any imports are available
- Use `torch.randn` for creating example tensors (not `torch.zeros` or `torch.ones`) to demonstrate behavior with realistic values
- Expected output lines (without `>>>`) show the actual result
- Multiple examples are separated by a blank line

## Notes and Warnings

Use `.. note::` for important behavioral details and `.. warning::` for potential pitfalls or breaking changes. These directives require a blank line after the directive and 4-space indentation for content:

```python
r"""
.. note::
    This function does not support complex tensors. Use :func:`torch.view_as_real`
    to convert before calling.

.. warning::
    In-place operations on tensors that require gradients will raise an error
    in autograd. Use the out-of-place variant instead.
"""
```

Place notes after the extended description but before Args. Place warnings immediately after the relevant parameter in Args if they are parameter-specific, or after notes if they are function-wide.

## In-Place Variants

Functions with in-place variants (suffixed with `_`) document both in the base function's docstring. The in-place variant's docstring should reference the base function rather than duplicating content:

```python
def relu_(input: Tensor) -> Tensor:
    r"""In-place version of :func:`~torch.nn.functional.relu`.

    See :func:`~torch.nn.functional.relu` for details.
    """
```

## C-Binding Documentation

For functions implemented in C++ with Python bindings, use `_add_docstr()` to attach documentation. The docstring content follows the same format rules:

```python
relu = _add_docstr(
    torch._C._nn.relu,
    r"""
relu(input, inplace=False) -> Tensor

Applies the rectified linear unit function element-wise.

See :class:`~torch.nn.ReLU` for more details.
""")
```

The first line of `_add_docstr` docstrings must be the function signature (name, params, return type annotation).

## Type Annotations in Docstrings

When the function signature already has Python type annotations, the Args section still includes types in parentheses for documentation completeness. The docstring types should match the signature types exactly — do not simplify or expand them:

```python
def linear(input: Tensor, weight: Tensor, bias: Optional[Tensor] = None) -> Tensor:
    r"""Applies a linear transformation.

    Args:
        input (Tensor): input tensor of shape :math:`(*, \text{in\_features})`
        weight (Tensor): weight matrix of shape :math:`(\text{out\_features}, \text{in\_features})`
        bias (Optional[Tensor]): optional bias. Default: ``None``
    """
```

## Returns Section

The Returns section documents the output type and semantics. For functions returning a single tensor, include the output shape:

```python
r"""
Returns:
    Tensor: the pooled output tensor of shape :math:`(N, C, H_{out}, W_{out})` where

    .. math::
        H_{out} = \left\lfloor\frac{H_{in} + 2 \times \text{padding} - \text{kernel\_size}}{\text{stride}} + 1\right\rfloor
"""
```

For named tuples or multiple returns, document each field on its own line with 4-space indent.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Math not rendering | Check for `r"""` prefix; verify backslashes aren't being escaped |
| Broken cross-reference | Ensure target is documented and importable; check for typos in path |
| Doctest failures | Verify imports are included; check tensor shapes match expected output |
| Indentation warnings | Args uses 4-space indent; continuations use 8-space |
| Build warnings about duplicate | Use `~` prefix to disambiguate short names |

## References

- `torch/_tensor_docs.py` — Tensor method docstrings
- `torch/nn/functional.py` — Functional API docstrings  
- Sphinx reStructuredText documentation
- PyTorch documentation style guide (internal wiki)
