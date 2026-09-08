"""Regressionstests für Segmentierung und Trial-Analysen (Review #7, #8, #9)."""

from __future__ import annotations

from src.analysis.statistics import baseline_vs_task, event_density
from src.models.experiment_records import (
    EventRecord,
    EventType,
    SensorStreamRecord,
    TrialRecord,
)
from src.preprocessing.segmentation import build_timeline


def _ev(ts, etype, label, meta=None):
    return EventRecord(ts, etype, label, meta or {})


class TestDomainPairing:
    """Bug 7: asymmetrische Domain-Metadaten dürfen die Paarung nicht brechen."""

    def test_domain_only_on_start_pairs_correctly(self):
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": "gaming"}),
            _ev(100, EventType.TASK_END, "task:end", {}),  # keine Domain
        ]
        tl = build_timeline("X", ev)
        assert [(s.domain, s.is_complete) for s in tl.segments] == [("gaming", True)]
        assert tl.quality_issues == []

    def test_domain_only_on_end_pairs_correctly(self):
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": "gaming"}),
        ]
        tl = build_timeline("X", ev)
        assert [(s.domain, s.is_complete) for s in tl.segments] == [("gaming", True)]

    def test_cross_domain_mispairing_still_prevented(self):
        # END mit Domain passt nur auf Starts dieser Domain (oder ohne Domain)
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": "gaming"}),
            _ev(50, EventType.TASK_START, "task:start", {"domain": "health"}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": "health"}),
            _ev(150, EventType.TASK_END, "task:end", {"domain": "city"}),
        ]
        tl = build_timeline("X", ev)
        segs = sorted((s.domain, s.is_complete) for s in tl.segments)
        assert segs == [("gaming", False), ("health", True)]
        assert any("Orphaned END" in i for i in tl.quality_issues)

    def test_start_without_domain_is_claimable_by_any_end(self):
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {}),          # keine Domain
            _ev(100, EventType.TASK_END, "task:end", {"domain": "city"}),
        ]
        tl = build_timeline("X", ev)
        assert [(s.is_complete) for s in tl.segments] == [True]

    def test_empty_domain_string_behaves_like_none(self):
        # Review2 #7: "" / " " sind semantisch 'keine Domain' und müssen
        # mit einem Ende mit echter Domain paaren können.
        for empty in ("", "   "):
            ev = [
                _ev(0, EventType.TASK_START, "task:start", {"domain": empty}),
                _ev(100, EventType.TASK_END, "task:end", {"domain": "gaming"}),
            ]
            tl = build_timeline("X", ev)
            assert [(s.domain, s.is_complete) for s in tl.segments] == \
                [("gaming", True)], f"domain={empty!r} wurde nicht wie None behandelt"
            assert tl.quality_issues == []

    def test_empty_domain_on_end_pairs_with_domain_start(self):
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": "gaming"}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": " "}),
        ]
        tl = build_timeline("X", ev)
        assert [(s.domain, s.is_complete) for s in tl.segments] == [("gaming", True)]

    def test_domain_values_are_trimmed(self):
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": "  gaming  "}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": "gaming"}),
        ]
        tl = build_timeline("X", ev)
        assert tl.segments[0].domain == "gaming"


class TestEventDensity:
    """Bug 9: Grenzereignisse dürfen nicht doppelt gezählt werden."""

    def _trial_with_boundary_event(self):
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {}),
            _ev(100, EventType.TASK_END, "task:end", {}),
            _ev(100, EventType.TASK_START, "task:start", {}),  # gleicher Timestamp
            _ev(200, EventType.TASK_END, "task:end", {}),
        ]
        return TrialRecord("T9", "/x", events=ev), build_timeline("T9", ev)

    def test_boundary_event_counted_exactly_once(self):
        trial, tl = self._trial_with_boundary_event()
        df = event_density(tl, trial)
        seg_rows = df[df["segment"] != "<gesamt>"]
        assert seg_rows["n_events"].tolist() == [2, 2], \
            f"Grenzereignis doppelt gezählt: {seg_rows['n_events'].tolist()}"
        assert df.iloc[0]["n_events"] == 4  # Gesamtzeile bleibt 4

    def test_segment_counts_sum_to_at_most_total(self):
        trial, tl = self._trial_with_boundary_event()
        df = event_density(tl, trial)
        seg_rows = df[df["segment"] != "<gesamt>"]
        assert seg_rows["n_events"].sum() <= df.iloc[0]["n_events"]


class TestBaselineVsTask:
    """Bug 8: Gruppierung nach segment_type, nicht nach Label."""

    def _stream(self):
        # 5 s à 10 Hz: 0–2 s Baseline-Wert 1.0, 2–5 s Task-Wert 3.0
        ts = [float(i * 100) for i in range(50)]
        vals = [1.0 if t < 2000 else 3.0 for t in ts]
        return SensorStreamRecord(source="s", modality="m",
                                  timestamps=ts, channels={"v": vals})

    def _timeline_nonstandard_labels(self):
        # Baseline heißt 'rest', Task heißt 'arbeit' — Labels, nicht Typen.
        # Kleine Lücke zwischen den Segmenten, damit der Grenzsample nicht
        # (geschlossenem Intervall folgend) in beide Segmente fällt.
        ev = [
            _ev(0, EventType.BASELINE_START, "rest:start", {}),
            _ev(1900, EventType.BASELINE_END, "rest:end", {}),
            _ev(2000, EventType.TASK_START, "arbeit:start", {}),
            _ev(4900, EventType.TASK_END, "arbeit:end", {}),
        ]
        return build_timeline("X", ev)

    def test_groups_by_segment_type_not_label(self):
        df = baseline_vs_task(self._timeline_nonstandard_labels(), self._stream())
        row = df[df["channel"] == "v"].iloc[0]
        assert row["baseline_mean"] == 1.0, \
            f"Baseline-Segment mit Label 'rest' nicht erkannt: {row.to_dict()}"
        assert row["task_mean"] == 3.0
        assert row["delta_task_minus_baseline"] == 2.0

    def test_repeated_segments_are_averaged_not_overwritten(self):
        # Zwei Baseline-Segmente (Wert 1.0 und 3.0) → Baseline-Mittel 2.0
        ev = [
            _ev(0, EventType.BASELINE_START, "baseline:start", {}),
            _ev(900, EventType.BASELINE_END, "baseline:end", {}),
            _ev(1100, EventType.BASELINE_START, "baseline:start", {}),
            _ev(1900, EventType.BASELINE_END, "baseline:end", {}),
            _ev(2100, EventType.TASK_START, "task:start", {}),
            _ev(2900, EventType.TASK_END, "task:end", {}),
        ]
        tl = build_timeline("X", ev)
        ts = [float(i * 100) for i in range(30)]
        vals = [1.0 if t < 1000 else (3.0 if t < 2000 else 5.0) for t in ts]
        stream = SensorStreamRecord(source="s", modality="m",
                                    timestamps=ts, channels={"v": vals})
        df = baseline_vs_task(tl, stream)
        row = df[df["channel"] == "v"].iloc[0]
        assert row["n_baseline_segments"] == 2, "wiederholtes Segment überschrieben"
        assert row["baseline_mean"] == 2.0
        assert row["task_mean"] == 5.0

    def test_channel_missing_in_one_segment_does_not_poison_mean(self):
        # Kanal 'w' fehlt im Task-Segment (leer) — Baseline-Mittel darf
        # nicht NaN werden; Task-Spalte bleibt ohne Werte
        ev = [
            _ev(0, EventType.BASELINE_START, "baseline:start", {}),
            _ev(900, EventType.BASELINE_END, "baseline:end", {}),
            _ev(1100, EventType.TASK_START, "task:start", {}),
            _ev(1900, EventType.TASK_END, "task:end", {}),
        ]
        tl = build_timeline("X", ev)
        ts = [float(i * 100) for i in range(20)]
        stream = SensorStreamRecord(
            source="s", modality="m", timestamps=ts,
            channels={"v": [1.0] * 10 + [4.0] * 10,
                      "w": [2.0] * 10 + [None] * 10},
        )
        df = baseline_vs_task(tl, stream)
        w = df[df["channel"] == "w"].iloc[0]
        assert w["baseline_mean"] == 2.0
        assert w["task_mean"] != w["task_mean"] or w["n_task_segments"] == 0
