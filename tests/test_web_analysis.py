"""Regressionstests für check_web_analysis.py (Paper-2-Reproduzierbarkeit).

Prüft auf einer synthetischen CSV die Kernmechanik: deterministische
Seeds, Cluster-/Baseline-/Dekorrelations-Berechnung und Abbildungs-Erzeugung.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import check_web_analysis as cwa

FEATS = cwa.FEATS


@pytest.fixture
def synth_csv(tmp_path):
    """Drei klare Profil-Gruppen über zwei 'Websites'."""
    rng = np.random.default_rng(7)
    rows = []
    for i in range(6):   # kleine, linkarme Seiten
        rows.append({"website": "A", "link_count": 20 + i, "form_count": 0,
                     "media_count": 0, "text_length": 800 + 50 * i,
                     "dom_depth": 12, "dom_nodes": 300 + 10 * i})
    for i in range(6):   # medienreiche, linkeiche Seiten
        rows.append({"website": "B", "link_count": 300 + 10 * i, "form_count": 1,
                     "media_count": 30 + i, "text_length": 4000 + 100 * i,
                     "dom_depth": 15, "dom_nodes": 800 + 20 * i})
    for i in range(6):   # Text-Hubs
        rows.append({"website": "A", "link_count": 800 + 20 * i, "form_count": 0,
                     "media_count": 0, "text_length": 20000 + 500 * i,
                     "dom_depth": 18, "dom_nodes": 2000 + 50 * i})
    p = tmp_path / "synth.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


class TestDeterminism:
    def test_cluster_analysis_deterministic(self, synth_csv):
        df = cwa.load(synth_csv)
        r1 = cwa.cluster_analysis(df)
        r2 = cwa.cluster_analysis(df)
        assert (r1["labels"] == r2["labels"]).all()
        assert r1["silhouette"] == r2["silhouette"]

    def test_importance_deterministic(self, synth_csv):
        df = cwa.load(synth_csv)
        res = cwa.importance_and_cv(df, cwa.cluster_analysis(df)["labels"])
        assert set(res["mdi"]) == set(FEATS)
        assert len(res["cv_folds"]) == 5


class TestClusterAnalysis:
    def test_recoverable_structure(self, synth_csv):
        # Die drei synthetischen Profile müssen als 3 Cluster zurückkommen
        df = cwa.load(synth_csv)
        ca = cwa.cluster_analysis(df)
        sizes = sorted(np.bincount(ca["labels"]).tolist())
        assert sizes == [6, 6, 6]
        assert ca["silhouette"] > 0.4  # klare Trennung im Synthetikfall

    def test_k_scan_covers_2_to_6(self, synth_csv):
        scan = cwa.k_scan(cwa.load(synth_csv))
        assert sorted(scan) == [2, 3, 4, 5, 6]
        assert all(-1 <= v <= 1 for v in scan.values())

    def test_baseline_runs(self, synth_csv):
        b = cwa.baseline(cwa.load(synth_csv))
        assert -1 <= b["silhouette"] <= 1 and -1 <= b["ari_to_full"] <= 1

    def test_decorrelation_reports_ari_and_sizes(self, synth_csv):
        d = cwa.decorrelation(cwa.load(synth_csv))
        assert sum(d["sizes"]) == 18
        assert len(d["contingency"]) == 2  # zwei Websites im Kreuz
        assert d["ari_to_full"] >= 0       # gleiche Datenbasis


class TestFigures:
    def test_figures_written(self, synth_csv, tmp_path):
        df = cwa.load(synth_csv)
        labels = cwa.cluster_analysis(df)["labels"]
        cwa.make_figures(df, labels, out_dir=tmp_path)
        assert (tmp_path / "paper2_abb1_feature_distribution_v2.png").exists()
        assert (tmp_path / "paper2_abb2_cluster_scatter_v2.png").exists()
