from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as Fnn

from . import config as C
from . import features as F
from .residual import ResidualTower


class PokemonAlphaZeroNet(nn.Module):
    """Policy / value network used by the search."""

    def __init__(self,
                 input_dim: int = F.FEATURE_DIM,
                 hidden: int = C.NETWORK_HIDDEN,
                 blocks: int = C.NETWORK_BLOCKS,
                 n_actions: int = C.N_ACTIONS,
                 policy_hidden: int = C.POLICY_HIDDEN,
                 value_hidden: int = C.VALUE_HIDDEN,
                 use_bn: bool = C.NETWORK_USE_BN,
                 dropout: float = C.NETWORK_DROPOUT):
        super().__init__()
        self.input_dim   = input_dim
        self.n_actions   = n_actions
        self.hidden_dim  = hidden

        self.stem = nn.Sequential(
            nn.Linear(input_dim, hidden, bias=not use_bn),
            nn.BatchNorm1d(hidden) if use_bn else nn.Identity(),
            nn.ReLU(inplace=True),
        )
        # pyrefly: ignore [bad-argument-type]
        nn.init.kaiming_normal_(self.stem[0].weight, nonlinearity="relu")
        if self.stem[0].bias is not None:
            # pyrefly: ignore [bad-argument-type]
            nn.init.zeros_(self.stem[0].bias)

        self.body = ResidualTower(hidden, blocks, use_bn=use_bn, dropout=dropout)

        self.policy_head = nn.Sequential(
            nn.Linear(hidden, policy_hidden, bias=not use_bn),
            nn.BatchNorm1d(policy_hidden) if use_bn else nn.Identity(),
            nn.ReLU(inplace=True),
            nn.Linear(policy_hidden, n_actions),
        )
        for m in self.policy_head:
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

        self.value_head = nn.Sequential(
            nn.Linear(hidden, value_hidden, bias=not use_bn),
            nn.BatchNorm1d(value_hidden) if use_bn else nn.Identity(),
            nn.ReLU(inplace=True),
            nn.Linear(value_hidden, 1),
            nn.Tanh(),
        )
        for m in self.value_head:
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:  # type: ignore[override]
        """Return ``(policy_logits, value)``."""
        h = self.stem(x)
        h = self.body(h)
        policy_logits = self.policy_head(h)
        value         = self.value_head(h).squeeze(-1)
        return policy_logits, value

    @torch.inference_mode()
    def predict_batch(self,
                      states: np.ndarray,
                      masks:  np.ndarray | None = None,
                      device: torch.device | None = None
                      ) -> Tuple[np.ndarray, np.ndarray]:
        """Run a batched forward pass and return ``(policy, value)`` as numpy.

        ``policy`` is post-softmax probability with illegal entries zeroed
        and re-normalised to sum to 1.
        """
        if device is None:
            device = next(self.parameters()).device
        was_training = self.training
        if was_training:
            self.eval()
        try:
            x = torch.as_tensor(states, dtype=torch.float32, device=device)
            if x.ndim == 1:
                x = x.unsqueeze(0)
            logits, value = self.forward(x)
            if masks is not None:
                m = torch.as_tensor(masks, dtype=torch.bool, device=device)
                if m.ndim == 1:
                    m = m.unsqueeze(0)
                neg_inf = torch.finfo(logits.dtype).min
                logits = torch.where(m, logits, torch.full_like(logits, neg_inf))
            probs = Fnn.softmax(logits, dim=-1)
            if masks is not None:
                # pyrefly: ignore [unbound-name]
                probs = probs * m.float()
                probs = probs / probs.sum(dim=-1, keepdim=True).clamp_min(1e-12)
            return probs.detach().cpu().numpy().astype(np.float32), value.detach().cpu().numpy().astype(np.float32)
        finally:
            if was_training:
                self.train()

    def count_parameters(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.parameters())
        train = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {"total": total, "trainable": train}


def build_default_network() -> PokemonAlphaZeroNet:
    """Construct the default-config network on the best available device."""
    net = PokemonAlphaZeroNet()
    dev = C.torch_device()
    net.to(dev)
    return net


__all__ = ["PokemonAlphaZeroNet", "build_default_network"]
