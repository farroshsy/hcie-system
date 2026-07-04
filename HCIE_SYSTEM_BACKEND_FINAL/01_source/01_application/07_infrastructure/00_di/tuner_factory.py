"""Transfer weight tuner factory.

`TransferWeightTuner` lives in the experiment layer
(`experiments/transfer_weight_tuner.py`) and already satisfies
`TransferWeightTunerProtocol` (see `tools/migrate/check_protocols.py`).
"""

from __future__ import annotations

from typing import Any


def build_transfer_weight_tuner(*, smoothing_alpha: float = 0.1, min_samples: int = 5) -> Any:
    from experiments.transfer_weight_tuner import TransferWeightTuner
    return TransferWeightTuner(smoothing_alpha=smoothing_alpha, min_samples=min_samples)
