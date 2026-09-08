"""Loader for experiment trial folders.

Expected folder layout:
  <trial_dir>/
    events.ndjson
    fusion_merged.ndjson   (NDJSON or JSON array)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.loaders.sort_utils import natural_sort_key
from src.models.experiment_records import (
    EventRecord,
    EventType,
    SensorStreamRecord,
    TrialRecord,
)

# ── Event-type classification ─────────────────────────────────────────────────

_EVENT_KEYWORDS: list[tuple[EventType, list[str]]] = [
    (EventType.TASK_START,           ["task_start", "taskstart", "task start", "task_begin"]),
    (EventType.TASK_END,             ["task_end", "taskend", "task end", "task_stop"]),
    (EventType.BASELINE_START,       ["baseline_start", "baseline start", "base_start"]),
    (EventType.BASELINE_END,         ["baseline_end", "baseline end", "base_end"]),
    (EventType.QUESTIONNAIRE_START,  ["questionnaire_start", "questionnaire start", "survey_start"]),
    (EventType.QUESTIONNAIRE_END,    ["questionnaire_end", "questionnaire end", "survey_end"]),
]


def _classify(label: str) -> EventType:
    # Normalise separators: "baseline:start" → "baseline_start"
    lower = label.lower().replace("-", "_").replace(":", "_")
    for event_type, keywords in _EVENT_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return event_type
    return EventType.UNKNOWN


# ── NDJSON helpers ────────────────────────────────────────────────────────────

def _read_ndjson(path: str) -> list[dict[str, Any]]:
    """Parse NDJSON (one JSON object per line) or a plain JSON array."""
    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        content = fh.read().strip()

    if content.startswith("["):
        # Plain JSON array
        return json.loads(content)

    for line in content.splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


_TS_KEYS: tuple[str, ...] = ("timestamp", "ts", "time", "t", "Timestamp", "Time")

# Normalisierte Formen (klein, ohne Separatoren) der erlaubten Timestamp-Keys:
# erfasst auch timestamp_ms / timestampMs / ts_ms / TimeMs etc.
_TS_KEYS_NORMALIZED: set[str] = {"ts", "t", "time", "timestamp", "timestampms", "tsms", "timems"}


def _normalize_key(key: str) -> str:
    return key.lower().replace("_", "").replace("-", "")


def _timestamp_key_and_value(obj: dict[str, Any]) -> tuple[str | None, float | None]:
    """
    Liefert (Schlüssel, Wert) des Record-Timestamps einer Zeile.
    Exakte Treffer zuerst (bestehende Priorität), danach normalisierte
    Varianten wie timestamp_ms / timestampMs. Der Schlüssel wird mit
    zurückgegeben, damit er konsistent aus meta entfernt werden kann.
    """
    candidates = [k for k in _TS_KEYS if k in obj]
    candidates += [
        k for k in obj
        if k not in _TS_KEYS and _normalize_key(k) in _TS_KEYS_NORMALIZED
    ]
    for key in candidates:
        try:
            return key, float(obj[key])
        except (TypeError, ValueError):
            pass
    return None, None


def _is_timestamp_alias(key: str) -> bool:
    """True, wenn der Schlüssel ein Timestamp-Alias ist (exakt oder in
    normalisierter Form wie timestamp_ms / ts_ms / TimeMs)."""
    return key in _TS_KEYS or _normalize_key(key) in _TS_KEYS_NORMALIZED


def _extract_timestamp(obj: dict[str, Any]) -> float | None:
    return _timestamp_key_and_value(obj)[1]


def _extract_label(obj: dict[str, Any]) -> str:
    for key in ("event", "type", "label", "name", "event_type", "eventType", "Event"):
        if key in obj:
            return str(obj[key])
    return str(obj)


# ── Core parsers ──────────────────────────────────────────────────────────────

def _parse_events(path: str) -> list[EventRecord]:
    events: list[EventRecord] = []
    for obj in _read_ndjson(path):
        ts = _extract_timestamp(obj)
        if ts is None:
            continue
        label = _extract_label(obj)
        # ALLE vorhandenen Timestamp-Aliase werden aus meta entfernt — auch
        # die nicht ausgewählten (z. B. gleichzeitig 'ts' und 'timestamp_ms'
        # in einer Zeile), und auch solche, deren Wert nicht konvertierbar
        # war und deshalb einen anderen Alias zur Timestamp-Quelle machte.
        meta = {k: v for k, v in obj.items()
                if not _is_timestamp_alias(k) and k not in ("event", "type", "label", "name")}
        events.append(EventRecord(
            timestamp=ts,
            event_type=_classify(label),
            label=label,
            meta=meta,
        ))
    events.sort(key=lambda e: e.timestamp)
    return events


def _flatten(obj: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Recursively flatten nested dicts with dot-notation keys."""
    result: dict[str, Any] = {}
    for key, val in obj.items():
        full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        if isinstance(val, dict):
            result.update(_flatten(val, full_key))
        else:
            result[full_key] = val
    return result


_SKIP_KEYS = {"rate_hz", "fresh_shimmer", "fresh_gaze", "ts_iso", "trialid", "fusionconf"}

# Blattnamen, die genau einem Timestamp-Alias entsprechen (normalisiert):
# ts, t, time, timestamp, timestamp_ms, ts_ms, timeMs, …
_TS_LEAF_EXACT: set[str] = set(_TS_KEYS_NORMALIZED)

# Zusammengesetzte Uhrfelder bekannter Quellen: <prefix>timestamp(ms).
# Nur diese Präfixe gelten als Clock-Feld — Kanäle wie 'heart_timestamp'
# sind Signale und bleiben erhalten.
_TS_CLOCK_PREFIXES: tuple[str, ...] = (
    "app", "system", "sample", "sensor", "frame", "record", "event",
    "device", "capture", "unix", "epoch", "server", "client", "log",
    "source", "sent", "receive",
)


def _is_clock_field(compact_leaf: str) -> bool:
    if compact_leaf in _TS_LEAF_EXACT:
        return True
    return any(
        compact_leaf == f"{prefix}{suffix}"
        for prefix in _TS_CLOCK_PREFIXES
        for suffix in ("timestampms", "timestamp")
    )


def _is_skippable(key: str) -> bool:
    base = key.split(".")[-1].lower()  # last segment for skip-check
    compact = base.replace("_", "").replace("-", "")
    return (
        key in _TS_KEYS
        or base in _TS_KEYS
        or base in _SKIP_KEYS
        or _is_clock_field(compact)
    )


def _parse_sensor_stream(path: str) -> SensorStreamRecord:
    """
    Parse fusion_merged.ndjson into a SensorStreamRecord.

    Nested objects (shimmer, gaze, …) are flattened with dot-notation keys.
    Only numeric leaf values become channels. Records may carry different
    subsets of keys (e.g. modality-specific fusion rows); every channel is
    padded with None so it stays parallel with `timestamps` (see
    SensorStreamRecord's documented invariant).
    """
    parsed: list[tuple[float, dict[str, Any]]] = []
    for obj in _read_ndjson(path):
        ts = _extract_timestamp(obj)
        if ts is None:
            continue
        parsed.append((ts, _flatten(obj)))

    # First pass: which keys ever hold a numeric value → become channels.
    channel_keys: set[str] = set()
    skipped_keys: set[str] = set()
    for _, flat in parsed:
        for key, val in flat.items():
            if _is_skippable(key) or key in channel_keys:
                continue
            try:
                float(val)
                channel_keys.add(key)
            except (TypeError, ValueError):
                skipped_keys.add(key)
    skipped_keys -= channel_keys

    # Second pass: build parallel arrays (None where a record lacks the key).
    timestamps: list[float] = []
    channels: dict[str, list[Any]] = {key: [] for key in channel_keys}
    for ts, flat in parsed:
        timestamps.append(ts)
        for key in channel_keys:
            val = flat.get(key)
            try:
                channels[key].append(float(val))
            except (TypeError, ValueError):
                channels[key].append(None)

    return SensorStreamRecord(
        source=Path(path).stem,
        modality="fusion",
        timestamps=timestamps,
        channels=channels,
        meta={"skipped_non_numeric_keys": sorted(skipped_keys)} if skipped_keys else {},
    )


# ── Public API ────────────────────────────────────────────────────────────────

def load_trial(trial_dir: str) -> TrialRecord:
    """Load a single trial folder into a TrialRecord."""
    p = Path(trial_dir)
    trial_id = p.name

    events: list[EventRecord] = []
    streams: list[SensorStreamRecord] = []

    events_path = p / "events.ndjson"
    if events_path.exists():
        events = _parse_events(str(events_path))

    fusion_path = p / "fusion_merged.ndjson"
    if fusion_path.exists():
        streams.append(_parse_sensor_stream(str(fusion_path)))

    return TrialRecord(
        trial_id=trial_id,
        source_dir=str(p.resolve()),
        events=events,
        streams=streams,
    )


def load_trials_from_dir(parent_dir: str) -> list[TrialRecord]:
    """
    Scan parent_dir for sub-folders and load each as a TrialRecord.
    Sub-folders are included if they contain at least one of the expected files.
    """
    p = Path(parent_dir)
    trials: list[TrialRecord] = []

    for entry in sorted(p.iterdir(), key=lambda e: natural_sort_key(e.name)):
        if not entry.is_dir():
            continue
        has_events = (entry / "events.ndjson").exists()
        has_fusion = (entry / "fusion_merged.ndjson").exists()
        if has_events or has_fusion:
            trials.append(load_trial(str(entry)))

    return trials
