"""Loader for experiment trial folders.

Expected folder layout (kanonische Namen, aber keine harte Bindung —
siehe find_event_file/find_sensor_files):
  <trial_dir>/
    events.ndjson            (oder events.json / events*.ndjson)
    fusion_merged.ndjson     (oder .json; weitere fusion*/openbci*/sensor*-
                             Quellen werden zusätzlich als eigene Streams
                             geladen, siehe sensor_loader)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.loaders.sensor_loader import (  # noqa: F401  (re-export für Kompatibilität)
    _extract_timestamp,
    _is_timestamp_alias,
    _is_skippable,
    _read_ndjson,
    _timestamp_key_and_value,
    find_sensor_files,
    load_sensor_streams,
    parse_sensor_stream,
)
from src.loaders.sort_utils import natural_sort_key
from src.models.experiment_records import (
    EventRecord,
    EventType,
    SensorStreamRecord,
    TrialRecord,
)

# Kompatibilitäts-Alias: bisherige Aufrufer (inkl. Tests) importieren
# _parse_sensor_stream aus dem trial_loader.
_parse_sensor_stream = parse_sensor_stream

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


# ── Event-file discovery (keine harte Dateinamen-Bindung, AP3) ───────────────

_EVENT_SUFFIXES = {".ndjson", ".json"}


def find_event_file(trial_dir: str | Path) -> Path | None:
    """
    Event-Log eines Trial-Ordners finden.

    Bevorzugt: events.ndjson, events.json; danach beliebige events*-
    Dateien mit den Endungen .ndjson/.json (z. B. events_t1.ndjson).
    """
    p = Path(trial_dir)
    for canonical in ("events.ndjson", "events.json"):
        candidate = p / canonical
        if candidate.is_file():
            return candidate
    if not p.is_dir():
        return None
    for f in sorted(p.iterdir(), key=lambda e: e.name):
        if f.is_file() and f.stem.lower().startswith("events") \
                and f.suffix.lower() in _EVENT_SUFFIXES:
            return f
    return None


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


# ── Public API ────────────────────────────────────────────────────────────────

def load_trial(trial_dir: str) -> TrialRecord:
    """Load a single trial folder into a TrialRecord."""
    p = Path(trial_dir)
    trial_id = p.name

    events: list[EventRecord] = []
    if (events_path := find_event_file(p)) is not None:
        events = _parse_events(str(events_path))

    streams: list[SensorStreamRecord] = load_sensor_streams(p)

    return TrialRecord(
        trial_id=trial_id,
        source_dir=str(p.resolve()),
        events=events,
        streams=streams,
    )


def load_trials_from_dir(parent_dir: str) -> list[TrialRecord]:
    """
    Scan parent_dir for sub-folders and load each as a TrialRecord.
    Sub-folders are included if they contain at least one recognizable
    event or sensor file (kanonische Namen oder Muster).
    """
    p = Path(parent_dir)
    trials: list[TrialRecord] = []

    for entry in sorted(p.iterdir(), key=lambda e: natural_sort_key(e.name)):
        if not entry.is_dir():
            continue
        if find_event_file(entry) is not None or find_sensor_files(entry):
            trials.append(load_trial(str(entry)))

    return trials
