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


class TestNumericDomainPairing:
    """Review3 #3: nicht-stringartige Domains (z. B. 1 und 2 bei offenen
    Starts) dürfen nicht wie fehlende Domains (None) behandelt werden,
    sonst paart ein Ende fälschlich mit dem ersten fremden Start."""

    def test_numeric_domains_do_not_cross_pair(self):
        # Vorher: beide Starts wurden zu Domain None normalisiert → das END
        # für Domain 2 paarte mit dem ältesten Start (Domain 1).
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": 1}),
            _ev(50, EventType.TASK_START, "task:start", {"domain": 2}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": 2}),
            _ev(150, EventType.TASK_END, "task:end", {"domain": 1}),
        ]
        tl = build_timeline("X", ev)
        segs = sorted((s.start_ms, s.domain, s.is_complete) for s in tl.segments)
        assert segs == [
            (0, "1", True),    # END 150 gehört zu Start mit Domain 1
            (50, "2", True),   # END 100 gehört zu Start mit Domain 2
        ], f"Fehlpaarung numerischer Domains: {segs}"
        # Verschachtelte Paarungen überlappen zeitlich zwangsläufig — die
        # Overlap-Meldung ist korrekt; entscheidend ist, dass KEIN Event
        # verwaist oder ungepaart bleibt.
        assert not any("Orphaned" in i or "Missing END" in i
                       for i in tl.quality_issues), tl.quality_issues

    def test_numeric_domain_not_treated_as_missing(self):
        # Ein END mit Domain 2 darf einen START ohne Domain nicht mehr
        # beanspruchen, wenn ein START mit Domain 2 wartet.
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {}),        # keine Domain
            _ev(50, EventType.TASK_START, "task:start", {"domain": 2}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": 2}),
        ]
        tl = build_timeline("X", ev)
        segs = sorted((s.start_ms, s.domain, s.is_complete) for s in tl.segments)
        assert segs == [(0, None, False), (50, "2", True)], \
            f"START ohne Domain hat den END von Domain 2 gestohlen: {segs}"

    def test_falsy_numeric_domain_zero_is_preserved(self):
        # 0 ist ein gültiger Domain-Wert und darf nicht wie 'fehlend' wirken
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": 0}),
            _ev(50, EventType.TASK_START, "task:start", {"domain": 7}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": 0}),
        ]
        tl = build_timeline("X", ev)
        segs = sorted((s.start_ms, s.domain, s.is_complete) for s in tl.segments)
        assert segs == [(0, "0", True), (50, "7", False)], \
            f"Domain 0 wurde wie None behandelt: {segs}"

    def test_numeric_and_string_domain_mixed_do_not_collide(self):
        # Numerisch 1 und String "2" sind verschiedene Domains und dürfen
        # nicht ineinander paarweise vermischt werden.
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": 1}),
            _ev(50, EventType.TASK_START, "task:start", {"domain": "2"}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": "2"}),
            _ev(150, EventType.TASK_END, "task:end", {"domain": 1}),
        ]
        tl = build_timeline("X", ev)
        segs = sorted((s.start_ms, s.domain, s.is_complete) for s in tl.segments)
        assert segs == [(0, "1", True), (50, "2", True)]


class TestDomainNumericCanonicalization:
    """Review4: dieselbe Domain muss unabhängig von der Zahlendarstellung
    paarbar bleiben — int 1, float 1.0, "1", "1.0", "01", "1e0" sind alle
    Domain 1; 1.5, "1.50" sind Domain 1.5."""

    CASES = [
        (1, 1.0, "1"),
        (1, "1", "1"),
        ("1", 1.0, "1"),
        ("1.0", 1, "1"),
        ("01", 1.0, "1"),
        ("1e0", 1, "1"),
        (1.5, "1.50", "1.5"),
        (-1, "-1.0", "-1"),
        (-2.5, -2.5, "-2.5"),
        ("1e3", 1000, "1000"),
    ]

    def test_equivalent_representations_pair(self):
        from src.preprocessing.segmentation import _domain_of
        for a, b, expected in self.CASES:
            got_a, got_b = _domain_of({"domain": a}), _domain_of({"domain": b})
            assert got_a == got_b == expected, \
                f"{a!r} und {b!r} normalisieren unterschiedlich: {got_a!r} vs {got_b!r}"

    def test_int_and_float_domain_pair_in_timeline(self):
        # Der konkrete Review-Fall: Start mit int 1, Ende mit float 1.0
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": 1}),
            _ev(50, EventType.TASK_START, "task:start", {"domain": 2.0}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": 2.0}),
            _ev(150, EventType.TASK_END, "task:end", {"domain": 1.0}),
        ]
        tl = build_timeline("X", ev)
        segs = sorted((s.start_ms, s.domain, s.is_complete) for s in tl.segments)
        assert segs == [(0, "1", True), (50, "2", True)], \
            f"int/float-Domains paaren nicht: {segs}"

    def test_distinct_numeric_domains_stay_distinct(self):
        # Kanonisierung darf nicht über das Ziel hinausschießen
        from src.preprocessing.segmentation import _domain_of
        for a, b in [(1, 2), (1, 1.5), ("1", "2"), (-1, 1), (1.5, 1.501)]:
            assert _domain_of({"domain": a}) != _domain_of({"domain": b}), \
                f"{a!r} und {b!r} wurden fälschlich gleich normalisiert"

    def test_non_numeric_and_special_strings_untouched(self):
        from src.preprocessing.segmentation import _domain_of
        assert _domain_of({"domain": "gaming"}) == "gaming"
        assert _domain_of({"domain": "nan"}) == "nan"
        assert _domain_of({"domain": "inf"}) == "inf"
        assert _domain_of({"domain": True}) == "True"
        assert _domain_of({"domain": "  "}) is None
        assert _domain_of({}) is None

    def test_scientific_notation_pairing_end_to_end(self):
        ev = [
            _ev(0, EventType.TASK_START, "task:start", {"domain": 300}),
            _ev(50, EventType.TASK_START, "task:start", {"domain": 4}),
            _ev(100, EventType.TASK_END, "task:end", {"domain": "3e2"}),
            _ev(150, EventType.TASK_END, "task:end", {"domain": 4}),
        ]
        tl = build_timeline("X", ev)
        segs = sorted((s.start_ms, s.domain, s.is_complete) for s in tl.segments)
        assert segs == [(0, "300", True), (50, "4", True)], \
            f"'3e2' paart nicht mit 300: {segs}"


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
