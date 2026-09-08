"""AP6 – Time window generation from WindowDefinition + sensor streams."""

from __future__ import annotations

import numpy as np

from src.models.experiment_records import (
    SensorStreamRecord,
    TrialTimeline,
    WindowDefinition,
)


def generate_windows(
    stream: SensorStreamRecord,
    definition: WindowDefinition,
    timeline: TrialTimeline | None = None,
) -> list[tuple[float, float]]:
    """
    Return a list of (start_ms, end_ms) tuples for the given definition.

    mode="fixed"   – single window anchored at stream start
    mode="sliding" – sweep across full stream
    mode="task"    – one window per matching segment in the timeline
    """
    if not stream.timestamps:
        return []

    t_min = min(stream.timestamps)
    t_max = max(stream.timestamps)

    if definition.mode == "fixed":
        if definition.duration_ms <= 0:
            raise ValueError(f"WindowDefinition.duration_ms must be > 0, got {definition.duration_ms}")
        start = t_min + definition.offset_start_ms
        end = start + definition.duration_ms + definition.offset_end_ms
        end_clamped = min(end, t_max)
        if end_clamped <= start:
            raise ValueError(
                f"Leeres fixed-Fenster: start={start:.0f} ms liegt nicht vor Ende "
                f"{end_clamped:.0f} ms (offset_start zu groß oder Stream zu kurz)."
            )
        return [(start, end_clamped)]

    elif definition.mode == "sliding":
        step = definition.step_ms or definition.duration_ms
        if step <= 0:
            raise ValueError(f"WindowDefinition.step_ms/duration_ms must be > 0, got step={step}")
        if definition.duration_ms <= 0:
            raise ValueError(f"WindowDefinition.duration_ms must be > 0, got {definition.duration_ms}")
        windows: list[tuple[float, float]] = []
        start = t_min
        while start + definition.duration_ms <= t_max:
            windows.append((start, start + definition.duration_ms))
            start += step
        return windows

    elif definition.mode == "task":
        if timeline is None:
            return []
        windows = []
        for seg in timeline.segments:
            if seg.label != definition.task_label or seg.end_ms is None:
                continue
            # Optional: nur Segmente einer bestimmten Domain (z. B. "gaming")
            if definition.task_domain and seg.domain != definition.task_domain:
                continue
            start = seg.start_ms + definition.offset_start_ms
            end = seg.end_ms + definition.offset_end_ms
            lo, hi = max(t_min, start), min(t_max, end)
            if hi <= lo:
                continue  # Segment liegt (nach Offsets) außerhalb des Streams
            windows.append((lo, hi))
        return windows

    raise ValueError(f"Unknown WindowDefinition.mode: {definition.mode!r}")


def slice_stream(
    stream: SensorStreamRecord,
    start_ms: float,
    end_ms: float,
) -> dict[str, list[float]]:
    """
    Return channel data within [start_ms, end_ms].
    Returns {"timestamps": [...], channel_name: [...], ...}
    """
    ts_arr = np.asarray(stream.timestamps)
    mask = (ts_arr >= start_ms) & (ts_arr <= end_ms)
    indices = np.flatnonzero(mask)

    result: dict[str, list] = {"timestamps": ts_arr[indices].tolist()}
    for ch, values in stream.channels.items():
        usable = indices[indices < len(values)]
        result[ch] = [values[i] for i in usable]
    return result
