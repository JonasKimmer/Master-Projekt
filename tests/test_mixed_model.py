"""Regressionstests für check_mixed_model.py (Paper-1-Reproduzierbarkeit).

Prüft auf synthetischen Trials die Kernmechanik: globaler Ausreißer-
Ausschluss, within-Person-Zentrierung und deterministischer Bootstrap.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

import check_mixed_model as cmm


def _write_trial(root: Path, trial_id: str, durations: dict[str, float],
                 tlx: dict[str, dict]) -> None:
    """Synthetischer Trial: je Domäne ein task:start/-end-Paar + TLX."""
    events, t = [], 1000.0
    for domain, dur in durations.items():
        events.append({"ts": t, "type": "task:start", "domain": domain})
        t += dur * 1000
        events.append({"ts": t, "type": "task:end", "domain": domain})
        t += 1000
    for domain, scores in tlx.items():
        events.append({"ts": t, "type": "tlx:submit", "domain": domain,
                       "scores": scores})
    d = root / trial_id
    d.mkdir(parents=True)
    (d / "events.ndjson").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")


class TestBuildFrame:
    def test_global_outlier_excluded(self, tmp_path):
        # Person OUT mit extremer Dauer → >3 SD → ausgeschlossen. Dafür
        # braucht es genug normale Records: bei n Werten ist die maximal
        # mögliche z-Distanz (n−1)/√n — erst ab ~11 normalen Werten kann
        # ein Ausreißer die 3-SD-Regel überhaupt reißen.
        for i in range(6):
            _write_trial(
                tmp_path, f"P-{i}",
                {"gaming": 60.0 + i, "health": 70.0 + i},
                {"gaming": {"frustration": 50, "mentale": 60, "anstrengung": 40},
                 "health": {"frustration": 55, "mentale": 62, "anstrengung": 42}},
            )
        _write_trial(tmp_path, "P-OUT", {"gaming": 90_000.0},
                     {"gaming": {"frustration": 50, "mentale": 60, "anstrengung": 40}})
        df = cmm.build_frame(tmp_path)
        assert "P-OUT" not in set(df["person"]), "3-SD-Ausreißer nicht ausgeschlossen"
        assert len(df) == 12

    def test_fisher_ci_covers_point_estimate(self):
        lo, hi = cmm.fisher_ci(0.56, 53)
        assert lo < 0.56 < hi


class TestCentering:
    def test_centering_removes_between_person_variance(self, tmp_path):
        # Zwischen Personen stark positiv (A niedrig-niedrig, B hoch-hoch),
        # innerhalb der Person negativ → zentriert muss r deutlich negativ
        # sein, unzentriert positiv.
        _write_trial(tmp_path, "P-A", {"gaming": 60.0, "health": 70.0},
                     {"gaming": {"frustration": 40, "mentale": 10, "anstrengung": 10},
                      "health": {"frustration": 20, "mentale": 10, "anstrengung": 10}})
        _write_trial(tmp_path, "P-B", {"gaming": 1060.0, "health": 1070.0},
                     {"gaming": {"frustration": 100, "mentale": 10, "anstrengung": 10},
                      "health": {"frustration": 80, "mentale": 10, "anstrengung": 10}})
        df = cmm.build_frame(tmp_path)
        uncentered = float(np.corrcoef(df["duration_s"], df["frustration"])[0, 1])
        centered = cmm.centered_r(df, "frustration")
        assert uncentered > 0.9
        assert centered < -0.9, \
            f"Zentrierung entfernt Personen-Varianz nicht: {centered:.2f}"

    def test_bootstrap_deterministic(self, tmp_path):
        _write_trial(tmp_path, "P-A", {"gaming": 60.0, "health": 70.0, "city": 80.0},
                     {d: {"frustration": 10 * i, "mentale": 5 * i, "anstrengung": 3 * i}
                      for i, d in enumerate(("gaming", "health", "city"))})
        _write_trial(tmp_path, "P-B", {"gaming": 90.0, "health": 100.0, "city": 110.0},
                     {d: {"frustration": 20 + 10 * i, "mentale": 15 + 5 * i, "anstrengung": 6 + 3 * i}
                      for i, d in enumerate(("gaming", "health", "city"))})
        df = cmm.build_frame(tmp_path)
        ci1 = cmm.clustered_bootstrap_ci(df, "frustration", n_resamples=50, seed=1)
        ci2 = cmm.clustered_bootstrap_ci(df, "frustration", n_resamples=50, seed=1)
        assert ci1 == ci2, "Bootstrap mit gleichem Seed muss deterministisch sein"
        assert ci1[0] <= ci1[1]
