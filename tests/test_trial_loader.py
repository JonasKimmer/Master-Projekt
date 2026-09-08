"""Regressionstests für das Timestamp-Handling im trial_loader (Review #3).

timestamp_ms / timestampMs / ts_ms dürfen weder als Sensor-Kanal importiert
werden noch als Record-Timestamp übersehen werden.
"""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from src.loaders.trial_loader import (
    _extract_timestamp,
    _is_skippable,
    _parse_events,
    _parse_sensor_stream,
    load_trials_from_dir,
)


def _write_ndjson(lines: list[dict]) -> str:
    fd, path = tempfile.mkstemp(suffix=".ndjson")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        for obj in lines:
            fh.write(json.dumps(obj) + "\n")
    return path


class TestTimestampKeys:
    def test_timestamp_ms_variants_recognized_as_record_timestamp(self):
        assert _extract_timestamp({"timestamp_ms": 1000, "type": "x"}) == 1000.0
        assert _extract_timestamp({"timestampMs": 1000}) == 1000.0
        assert _extract_timestamp({"ts_ms": 1000}) == 1000.0
        assert _extract_timestamp({"TimeMs": 1000}) == 1000.0
        # Bestehende Keys funktionieren weiter
        assert _extract_timestamp({"ts": 5}) == 5.0
        assert _extract_timestamp({"timestamp": 7}) == 7.0
        # Kein Timestamp-Key vorhanden
        assert _extract_timestamp({"value": 1.0}) is None

    def test_nested_timestamp_ms_not_a_sensor_channel(self):
        path = _write_ndjson([
            {"ts": 1000, "gaze": {"timestamp_ms": 995, "x": 0.5}},
            {"ts": 1100, "gaze": {"timestamp_ms": 1095, "x": 0.6}},
        ])
        try:
            stream = _parse_sensor_stream(path)
        finally:
            os.unlink(path)
        assert "gaze.x" in stream.channels
        assert not any("timestamp" in ch.lower() for ch in stream.channels), \
            f"Timestamp-Spur als Kanal importiert: {stream.channels}"

    def test_skippable_is_separator_insensitive(self):
        assert _is_skippable("gaze.timestamp_ms")
        assert _is_skippable("gaze.timestampMs")
        assert _is_skippable("shimmer.AppTimestampMs")  # bereits vorher gefixt
        assert _is_skippable("ts_iso")
        assert not _is_skippable("gaze.LeftX")           # echte Signale bleiben
        assert not _is_skippable("shimmer.GsrKOhm")

    def test_events_file_with_only_timestamp_ms_key(self):
        path = _write_ndjson([
            {"timestamp_ms": 1000, "type": "task:start"},
            {"timestamp_ms": 2000, "type": "task:end"},
        ])
        try:
            events = _parse_events(path)
        finally:
            os.unlink(path)
        assert len(events) == 2, "Events mit timestamp_ms-Schlüssel dürfen nicht verworfen werden"
        assert events[0].timestamp == 1000.0


class TestRealDataRegression:
    def test_18_trials_load_without_timestamp_channels(self):
        trials = load_trials_from_dir("data")
        assert len(trials) == 18
        for t in trials:
            for s in t.streams:
                for ch in s.channels:
                    assert "timestamp" not in ch.lower(), \
                        f"{t.trial_id}: {ch} wurde als Kanal importiert"
