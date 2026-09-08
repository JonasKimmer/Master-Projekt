"""Regressionstests für check_correlations.py (Review5 #5).

Das Skript speist Paper 1 und darf keine eigene Event-Parsing-Logik
pflegen: dieselben Timestamp-Aliase (ts, timestamp, timestamp_ms, …)
und Label-Keys (type, event, label, …) wie überall — also den
trial_loader- und segmentation-Vertrag — verwenden.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import check_correlations as cc


def _write_trial(root: Path, trial_id: str, events: list[dict]) -> None:
    d = root / trial_id
    d.mkdir(parents=True)
    (d / "events.ndjson").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
    )


ALIAS_EVENTS = [
    # Timestamp als timestamp_ms (nicht 'ts'), Label unter 'event'
    # (nicht 'type') — beides muss der Loader-Vertrag verarbeiten können.
    {"timestamp_ms": 1000,  "event": "task:start", "domain": "gaming"},
    {"timestamp_ms": 61000, "event": "task:end",   "domain": "gaming"},
    {"timestamp_ms": 70000, "event": "task:start", "domain": "gaming"},
    {"timestamp_ms": 95000, "event": "task:end",   "domain": "gaming"},
    {"timestamp_ms": 99000, "event": "tlx:submit", "domain": "gaming",
     "scores": {"frustration": 55, "mentale": 70}},
]


class TestCollectRecordsUsesLoaderContract:
    def test_alias_timestamps_and_label_keys_are_understood(self, tmp_path):
        _write_trial(tmp_path, "T-1", ALIAS_EVENTS)
        records = cc.collect_records(tmp_path)
        assert len(records) == 1, f"Alias-Events nicht erkannt: {records}"
        r = records[0]
        assert r["trial"] == "T-1"
        assert r["domain"] == "gaming"
        assert r["duration_s"] == pytest.approx(85.0)  # 60 s + 25 s
        assert r["frustration"] == 55
        assert r["mentale"] == 70

    def test_durations_sum_over_multiple_segments(self, tmp_path):
        _write_trial(tmp_path, "T-1", ALIAS_EVENTS)
        records = cc.collect_records(tmp_path)
        assert records[0]["duration_s"] == pytest.approx(85.0)

    def test_incomplete_segment_does_not_count(self, tmp_path):
        events = [
            {"ts": 0,     "type": "task:start", "domain": "health"},
            # kein task:end → Segment unvollständig, darf nicht zählen
            {"ts": 50000, "type": "tlx:submit", "domain": "health",
             "scores": {"frustration": 10, "mentale": 20}},
        ]
        _write_trial(tmp_path, "T-2", events)
        assert cc.collect_records(tmp_path) == []

    def test_tlx_without_matching_duration_is_skipped(self, tmp_path):
        events = [
            {"ts": 0, "type": "tlx:submit", "domain": "city",
             "scores": {"frustration": 5, "mentale": 6}},
        ]
        _write_trial(tmp_path, "T-3", events)
        assert cc.collect_records(tmp_path) == []

    def test_trials_without_events_file_are_skipped(self, tmp_path):
        (tmp_path / "leerer_ordner").mkdir()
        (tmp_path / "datei.txt").write_text("x")
        assert cc.collect_records(tmp_path) == []


class TestCompleteRecords:
    def test_none_scores_are_filtered(self):
        records = [
            {"trial": "A", "domain": "gaming", "duration_s": 60.0,
             "frustration": 55, "mentale": 70, "anstrengung": 40},
            {"trial": "B", "domain": "health", "duration_s": 30.0,
             "frustration": None, "mentale": 40, "anstrengung": 30},  # fehlender TLX-Wert
            {"trial": "C", "domain": "city", "duration_s": 45.0,
             "frustration": 20, "mentale": None, "anstrengung": 30},
        ]
        complete = cc.complete_records(records)
        assert [r["trial"] for r in complete] == ["A"]

    def test_missing_dimension_filters_record(self):
        # Ein Record ohne 'anstrengung' ist unvollständig und fällt raus
        records = [{"trial": "A", "domain": "gaming", "duration_s": 60.0,
                    "frustration": 55, "mentale": 70}]
        assert cc.complete_records(records) == []

    def test_numeric_strings_are_coerced(self):
        records = [{"trial": "A", "domain": "gaming", "duration_s": 60.0,
                    "frustration": "55", "mentale": 70.5, "anstrengung": "30"}]
        complete = cc.complete_records(records)
        assert complete[0]["frustration"] == 55.0
        assert complete[0]["mentale"] == 70.5
        assert complete[0]["anstrengung"] == 30.0
