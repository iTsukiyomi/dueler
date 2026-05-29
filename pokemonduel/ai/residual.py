from __future__ import annotations

import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    __slots__ = ()

    def __init__(self, dim: int, *, use_bn: bool = True, dropout: float = 0.0):
        super().__init__()
        self.fc1 = nn.Linear(dim, dim, bias=not use_bn)
        self.fc2 = nn.Linear(dim, dim, bias=not use_bn)
        self.bn1 = nn.BatchNorm1d(dim) if use_bn else nn.Identity()
        self.bn2 = nn.BatchNorm1d(dim) if use_bn else nn.Identity()
        self.act = nn.ReLU(inplace=True)
        self.drop = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        nn.init.kaiming_normal_(self.fc1.weight, nonlinearity="relu")
        nn.init.kaiming_normal_(self.fc2.weight, nonlinearity="relu")
        if self.fc1.bias is not None:
            nn.init.zeros_(self.fc1.bias)
        if self.fc2.bias is not None:
            nn.init.zeros_(self.fc2.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:           # type: ignore[override]
        h = self.fc1(x)
        h = self.bn1(h)
        h = self.act(h)
        h = self.drop(h)
        h = self.fc2(h)
        h = self.bn2(h)
        h = h + x
        return self.act(h)


class ResidualTower(nn.Module):
    """Stack of identical ``ResidualBlock`` modules."""

    def __init__(self, dim: int, blocks: int, *, use_bn: bool = True, dropout: float = 0.0):
        super().__init__()
        self.blocks = nn.Sequential(*[
            ResidualBlock(dim, use_bn=use_bn, dropout=dropout) for _ in range(blocks)
        ])

    def forward(self, x: torch.Tensor) -> torch.Tensor:           # type: ignore[override]
        return self.blocks(x)


__all__ = ["ResidualBlock", "ResidualTower"]
