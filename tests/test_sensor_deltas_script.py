"""Regressionstests für check_sensor_deltas.py (Paper-1-Skript, Abschnitt 4.4).

Prüft auf synthetischen Trials die Kernmechanik: Baseline-Auswahl (zwei
Baselines, nur die zweite überlappt den Stream — der T-3-Fall), Trial-Skip
ohne überlappende Baseline (der T-10-Fall), Deltas, pooled Statistik und
die Zählung negativer GSR-Samples.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import check_sensor_deltas as csd

T0 = 1_000_000.0  # ms


def _write_trial(root: Path, trial_id: str, *, stream_start: float,
                 two_baselines: bool, domains=("gaming", "health"),
                 negative_gsr: int = 0) -> None:
    """Synthetischer Trial: Baseline(s) + je 10 s Task pro Domäne."""
    events = []
    t = T0
    if two_baselines:
        events += [{"ts": t, "type": "baseline:start"}, {"ts": t + 30_000, "type": "baseline:end"}]
        t += 31_000  # zweite Baseline beginnt NACH stream_start
    events += [{"ts": t, "type": "baseline:start"}, {"ts": t + 30_000, "type": "baseline:end"}]
    baseline_window = (t, t + 30_000)
    t += 31_000
    for d in domains:
        events += [{"ts": t, "type": "task:start", "domain": d},
                   {"ts": t + 10_000, "type": "task:end", "domain": d}]
        t += 11_000

    # Fusions-Stream: 10 Hz ab stream_start über alle Events hinaus
    t_end = t + 1_000
    n = int((t_end - stream_start) / 100) + 1
    ts = [stream_start + i * 100 for i in range(n)]
    gsr, pupil_l, pupil_r = [], [], []
    neg_written = 0
    for x in ts:
        in_base = baseline_window[0] <= x <= baseline_window[1]
        gsr_val = 1.0 if in_base else 3.0          # Task: +2 µS über Baseline
        if not in_base and neg_written < negative_gsr:
            gsr_val = -0.5; neg_written += 1       # unmögliche negative Leitfähigkeit
        gsr.append(gsr_val)
        pupil_l.append(4.0 if in_base else 4.1)
        pupil_r.append(4.0 if in_base else 4.1)

    d = root / trial_id
    d.mkdir(parents=True)
    (d / "events.ndjson").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    rows = [{"ts": x, "shimmer": {"GsrConductanceUS": g, "PpgmV": 100.0},
             "gaze": {"LeftPupilDiamMm": pl, "RightPupilDiamMm": pr}}
            for x, g, pl, pr in zip(ts, gsr, pupil_l, pupil_r)]
    (d / "fusion_merged.ndjson").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


@pytest.fixture
def data_dir(tmp_path):
    # T-A: zwei Baselines, Stream überlappt nur die zweite (T-3-Muster)
    _write_trial(tmp_path, "T-A", stream_start=T0 + 31_000, two_baselines=True,
                 negative_gsr=3)
    # T-B: eine Baseline, Stream überlappt sie
    _write_trial(tmp_path, "T-B", stream_start=T0, two_baselines=False)
    # T-C: Stream beginnt NACH aller Baselines (T-10-Muster → kein Delta)
    _write_trial(tmp_path, "T-C", stream_start=T0 + 200_000, two_baselines=False)
    return tmp_path


class TestSensorDeltas:
    def test_second_baseline_used_when_first_misses_stream(self, data_dir):
        deltas = csd.sensor_deltas(data_dir)
        # T-A muss vertreten sein — nur die zweite Baseline überlappt den Stream
        gsr = deltas["Hautleitwert (µS)"]["gaming"]
        assert len(gsr) == 2, "T-A oder T-C fälschlich ein-/ausgeschlossen"
        # Task-Wert 3.0, Baseline 1.0 → Delta +2.0
        assert all(abs(v - 2.0) < 1e-9 for v in gsr)

    def test_trial_without_baseline_overlap_skipped(self, data_dir):
        deltas = csd.sensor_deltas(data_dir)
        for doms in deltas.values():
            for arr in doms.values():
                assert len(arr) == 2  # nur T-A und T-B, nicht T-C

    def test_deterministic(self, data_dir):
        a = {k: {d: v.tolist() for d, v in m.items()} for k, m in csd.sensor_deltas(data_dir).items()}
        b = {k: {d: v.tolist() for d, v in m.items()} for k, m in csd.sensor_deltas(data_dir).items()}
        assert a == b


class TestPooledAndNegatives:
    def test_pooled_descriptives_keys_and_min(self, data_dir):
        pooled = csd.pooled_descriptives(data_dir)
        assert "Hautleitwert (µS)" in pooled and "PPG-Rohsignal (mV)" in pooled
        # drei negative Samples wurden geschrieben → Minimum < 0
        assert pooled["Hautleitwert (µS)"]["min"] < 0

    def test_negative_gsr_count(self, data_dir):
        total, per_trial = csd.negative_gsr_samples(data_dir)
        assert total == 3 and per_trial == {"T-A": 3}
