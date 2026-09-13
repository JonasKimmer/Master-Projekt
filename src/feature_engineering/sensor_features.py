"""AP7 – Feature computation for sensor channel slices."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def compute_channel_features(values: list[Any]) -> dict[str, float]:
    """
    Compute standard features for a list of numeric (or None/unparseable) values.

    Enthält mit ``missing_rate`` die Fehlerrate (AP7): Anteil der Samples
    im Slice, die None/unparseable sind und damit in keine Kennzahl
    eingehen. Ist kein einziger Wert gültig, wird nur
    ``{"missing_rate": 1.0, "n_samples": 0.0}`` geliefert — der Kanal
    bleibt damit sichtbar, statt still zu verschwinden.
    """
    total = len(values)
    clean: list[float] = []
    for v in values:
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if math.isnan(fv):
            continue
        clean.append(fv)

    if not clean:
        if total:
            return {"missing_rate": 1.0, "n_samples": 0.0}
        return {}

    arr = np.asarray(clean, dtype=float)
    n = arr.size
    mean = float(arr.mean())
    std = float(arr.std(ddof=1)) if n > 1 else 0.0
    min_v = float(arr.min())
    max_v = float(arr.max())

    # Peak count: value higher than both neighbours
    peaks = int(np.sum((arr[1:-1] > arr[:-2]) & (arr[1:-1] > arr[2:])))

    # Trend: slope of simple linear regression (sample index as x)
    trend = float(np.polyfit(np.arange(n), arr, 1)[0]) if n > 1 else 0.0

    return {
        "mean":         round(mean, 6),
        "median":       round(float(np.median(arr)), 6),
        "std":          round(std, 6),
        "variance":     round(std ** 2, 6),
        "min":          round(min_v, 6),
        "max":          round(max_v, 6),
        "range":        round(max_v - min_v, 6),
        "peak_count":   float(peaks),
        "trend":        round(trend, 6),
        "n_samples":    float(n),
        "missing_rate": round(1.0 - n / total, 6) if total else 0.0,
    }


def compute_window_features(
    channel_data: dict[str, list],
    modality: str = "",
) -> dict[str, dict[str, float]]:
    """
    Compute features for all channels in a window slice.
    channel_data is the output of windowing.slice_stream().
    Returns {channel_name: {feature_name: value}}.
    """
    result: dict[str, dict[str, float]] = {}
    for key, values in channel_data.items():
        if key == "timestamps":
            continue
        feats = compute_channel_features(values)
        if feats:
            result[key] = feats
    return result
