import torch
import torch.nn as nn
from torch import Tensor
from typing import Optional, Tuple, Union


class DepthwiseSeparableConv2d(nn.Module):

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: Union[int, Tuple[int, int]] = 3,
        stride: Union[int, Tuple[int, int]] = 1,
        padding: Union[int, Tuple[int, int]] = 1,
        dilation: Union[int, Tuple[int, int]] = 1,
        bias: bool = True,
        padding_mode: str = "zeros",
        depth_multiplier: int = 1,
    ) -> None:
        super().__init__()
        self.depthwise = nn.Conv2d(
            in_channels,
            in_channels * depth_multiplier,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            dilation=dilation,
            groups=in_channels,
            bias=False,
            padding_mode=padding_mode,
        )
        self.pointwise = nn.Conv2d(
            in_channels * depth_multiplier,
            out_channels,
            kernel_size=1,
            bias=bias,
        )
        self.bn = nn.BatchNorm2d(out_channels)

    def forward(self, input: Tensor) -> Tensor:
        x = self.depthwise(input)
        x = self.pointwise(x)
        x = self.bn(x)
        return x
