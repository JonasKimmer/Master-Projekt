"""AP3/AP4 – Sensor-Stream-Loader.

Löst das Parsen von Sensor-Zeitreihen-Dateien aus dem Trial-Loader:

  * ``parse_sensor_stream(path, modality)`` – NDJSON/JSON-Array einer
    Sensorquelle (fusion_merged, OpenBCI, …) in ein SensorStreamRecord mit
    Punkt-Notations-Kanälen, None-Polsterung und Uhrfeld-Filterung
  * ``find_sensor_files(trial_dir)`` – erkennt Sensorquellen nach Muster,
    ohne harte Bindung an exakte Dateinamen (AP3)
  * ``load_sensor_streams(trial_dir)`` – alle erkannten Quellen eines
    Trial-Ordners als Liste (eine Quelle künftiger Sensor-Daten = ein
    zusätzlicher Stream, kein struktureller Umbau nötig)

Neue Quellen werden über ``_SENSOR_FILE_PATTERNS`` bekannt gemacht.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.experiment_records import SensorStreamRecord

# ── NDJSON / JSON-Array reader ────────────────────────────────────────────────

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


# ── Timestamp helpers (shared contract with the event parser) ────────────────

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


# ── Channel flattening & clock-field filtering ────────────────────────────────

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


# ── Stream parsing ────────────────────────────────────────────────────────────

def parse_sensor_stream(path: str, modality: str = "fusion") -> SensorStreamRecord:
    """
    Parse a sensor time-series file (NDJSON or JSON array) into a
    SensorStreamRecord.

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
        modality=modality,
        timestamps=timestamps,
        channels=channels,
        meta={"skipped_non_numeric_keys": sorted(skipped_keys)} if skipped_keys else {},
    )


# ── File discovery (keine harte Dateinamen-Bindung, AP3) ─────────────────────

_ALLOWED_SUFFIXES = {".ndjson", ".json"}

# (Muster, Modalität): erste Übereinstimmung gewinnt; Muster sind Prefixe,
# die per glob + Suffix-Filter geprüft werden.
_SENSOR_FILE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("fusion_merged", "fusion"),   # kanonischer Name der Fusionsquelle
    ("fusion", "fusion"),          # fusion_*.ndjson etc.
    ("openbci", "eeg"),            # künftige EEG-Quelle (Reservierung)
    ("sensor", "generic"),         # beliebige weitere Sensorquelle
)


def _match_modality(stem_lower: str) -> str | None:
    for prefix, modality in _SENSOR_FILE_PATTERNS:
        if stem_lower.startswith(prefix):
            return modality
    return None


def find_sensor_files(trial_dir: str | Path) -> list[tuple[Path, str]]:
    """
    Erkannte Sensor-Dateien eines Trial-Ordners als (Pfad, Modalität).

    Bevorzugt werden die kanonischen Namen (fusion_merged.ndjson/.json);
    danach Präfix-Muster (fusion*, openbci*, sensor*) mit den Endungen
    .ndjson/.json. Dateien, deren Blattname ein Event-Log ist, werden
    ausgeschlossen.
    """
    p = Path(trial_dir)
    if not p.is_dir():
        return []
    found: list[tuple[Path, str]] = []
    for f in sorted(p.iterdir(), key=lambda e: e.name):
        if not f.is_file() or f.suffix.lower() not in _ALLOWED_SUFFIXES:
            continue
        stem = f.stem.lower()
        if stem.startswith("events"):      # Event-Logs sind keine Sensorquellen
            continue
        modality = _match_modality(stem)
        if modality is not None:
            found.append((f, modality))
    return found


def load_sensor_streams(trial_dir: str | Path) -> list[SensorStreamRecord]:
    """Alle erkannten Sensor-Quellen eines Trial-Ordners als Streams."""
    return [parse_sensor_stream(str(path), modality)
            for path, modality in find_sensor_files(trial_dir)]
