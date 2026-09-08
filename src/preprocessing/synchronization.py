"""AP7 – Sensorfusion and temporal synchronisation.

Fusion streams mix modalities in one timestamp/channel table (e.g. the
Neurons-style ``fusion_merged.ndjson``: every row carries ``shimmer.*`` and
``gaze.*`` channels, or — in interleaved datasets — separate rows per source
with a common clock). This module

  * splits a fusion stream into per-modality streams (``split_fusion_stream``),
  * resamples a stream onto a uniform time grid (``resample_stream``),
  * aligns several streams to a common time base (``synchronize_streams``).

Resampling linearly interpolates numeric channels; gaps (missing values)
are left as None so downstream feature computation and quality checks still
see them.
"""

from __future__ import annotations

import numpy as np

from src.models.experiment_records import SensorStreamRecord, TrialRecord

# Channel prefix → modality label for split_fusion_stream()
_PREFIX_MODALITIES: dict[str, str] = {
    "shimmer": "shimmer_physio",   # GSR / PPG / IMU (Shimmer3)
    "gaze": "eye_tracking",
    "openbci": "eeg",              # future source, reserved
}


def split_fusion_stream(stream: SensorStreamRecord) -> list[SensorStreamRecord]:
    """
    Split a fusion stream into one SensorStreamRecord per channel prefix.

    Channels without a dot (top-level signals) stay in a "generic" stream.
    Rows in which the modality has no data at all are dropped, so each
    sub-stream keeps only its own effective samples.
    """
    groups: dict[str, dict[str, list]] = {}
    for ch_name in stream.channels:
        prefix = ch_name.split(".", 1)[0] if "." in ch_name else ""
        groups.setdefault(prefix, {})[ch_name] = stream.channels[ch_name]

    ts = stream.timestamps
    result: list[SensorStreamRecord] = []
    for prefix, channels in groups.items():
        # Keep only rows where at least one channel of this group has a value
        keep = [
            i for i in range(len(ts))
            if any(channels[c][i] is not None for c in channels)
        ]
        result.append(SensorStreamRecord(
            source=stream.source,
            modality=_PREFIX_MODALITIES.get(prefix, prefix or "generic"),
            timestamps=[ts[i] for i in keep],
            channels={c: [vals[i] for i in keep] for c, vals in channels.items()},
            sampling_rate_hz=stream.sampling_rate_hz,
            meta={"split_from_prefix": prefix or None},
        ))
    return result


def resample_stream(
    stream: SensorStreamRecord,
    target_hz: float,
    method: str = "linear",
    max_gap_ms: float | None = None,
) -> SensorStreamRecord:
    """
    Resample a stream onto a uniform grid at ``target_hz``.

    Numeric channels are interpolated (``method="linear"``) or
    nearest-neighbour filled (``method="nearest"``). Channels with fewer
    than two valid samples are carried over as all-None. Leading/trailing
    regions outside a channel's valid range stay None (no extrapolation),
    and grid points whose neighbouring valid samples are further away than
    ``max_gap_ms`` (default: two grid steps) also stay None — interpolating
    across large recording gaps would fabricate data.
    """
    if target_hz <= 0:
        raise ValueError(f"target_hz must be > 0, got {target_hz}")
    if not stream.timestamps:
        return SensorStreamRecord(
            source=stream.source, modality=stream.modality,
            timestamps=[], channels={c: [] for c in stream.channels},
            sampling_rate_hz=target_hz,
        )

    ts = np.asarray(stream.timestamps, dtype=float)
    t_min, t_max = float(ts.min()), float(ts.max())
    step_ms = 1000.0 / target_hz
    if max_gap_ms is None:
        max_gap_ms = 2.0 * step_ms
    grid = np.arange(t_min, t_max + step_ms / 2.0, step_ms)

    new_channels: dict[str, list] = {}
    for name, values in stream.channels.items():
        arr = np.asarray([np.nan if v is None else float(v) for v in values])
        valid = ~np.isnan(arr)
        if valid.sum() < 2:
            new_channels[name] = [None] * len(grid)
            continue
        tv, vv = ts[valid], arr[valid]
        if method == "nearest":
            idx = np.searchsorted(tv, grid).clip(1, len(tv) - 1)
            left, right = tv[idx - 1], tv[idx]
            choose_left = (grid - left) <= (right - grid)
            interp = np.where(choose_left, vv[idx - 1], vv[idx])
            dist = np.minimum(np.abs(grid - left), np.abs(right - grid))
        elif method == "linear":
            interp = np.interp(grid, tv, vv)
            idx = np.searchsorted(tv, grid).clip(1, len(tv) - 1)
            dist = np.maximum(grid - tv[idx - 1], tv[idx] - grid)
        else:
            raise ValueError(f"Unknown resample method: {method!r}")
        # No extrapolation and no interpolation across large gaps
        ok = (grid >= tv[0]) & (grid <= tv[-1]) & (dist <= max_gap_ms)
        interp = np.where(ok, interp, np.nan)
        new_channels[name] = [
            None if np.isnan(v) else round(float(v), 9) for v in interp
        ]

    return SensorStreamRecord(
        source=stream.source,
        modality=stream.modality,
        timestamps=[round(float(t), 6) for t in grid],
        channels=new_channels,
        sampling_rate_hz=target_hz,
        meta={**stream.meta, "resampled_to_hz": target_hz, "resample_method": method},
    )


def synchronize_streams(
    streams: list[SensorStreamRecord],
    target_hz: float,
    base: str = "earliest",
    method: str = "linear",
) -> list[SensorStreamRecord]:
    """
    Align several streams onto one shared uniform grid.

    ``base`` determines the grid origin:
      "earliest" – smallest timestamp across all streams (default)
      "latest"   – largest first timestamp (trim to common overlap)
    Each stream is shifted so its origin matches the grid origin, then
    resampled with ``resample_stream``.
    """
    if not streams:
        return []
    origins = [min(s.timestamps) for s in streams if s.timestamps]
    if not origins:
        return streams
    origin = min(origins) if base == "earliest" else max(origins)

    result: list[SensorStreamRecord] = []
    for s in streams:
        if not s.timestamps:
            result.append(s)
            continue
        if base == "latest":
            # Trim samples before the common overlap starts
            keep = [i for i, t in enumerate(s.timestamps) if t >= origin]
            trimmed = SensorStreamRecord(
                source=s.source, modality=s.modality,
                timestamps=[s.timestamps[i] for i in keep],
                channels={c: [vals[i] for i in keep] for c, vals in s.channels.items()},
            )
            result.append(resample_stream(trimmed, target_hz, method))
        else:
            result.append(resample_stream(s, target_hz, method))
    return result


def synchronize_trial(
    trial: TrialRecord,
    target_hz: float = 10.0,
    split_modalities: bool = True,
) -> list[SensorStreamRecord]:
    """
    Convenience wrapper: split a trial's fusion stream(s) into modalities
    and resample each onto a uniform grid at ``target_hz``.
    """
    out: list[SensorStreamRecord] = []
    for s in trial.streams:
        parts = split_fusion_stream(s) if split_modalities else [s]
        out.extend(resample_stream(p, target_hz) for p in parts)
    return out
