"""Regressionstests für src/analysis/ml_analysis.py (Review5 #4).

Kern: prepare_features muss feature_names NACH dropna(axis=1, how="all")
bilden — sonst stimmen Liste und Matrix nicht mehr überein und jede
Index-Zuordnung (Importances, Spaltenauswahl) verrutscht still.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.ml_analysis import prepare_features


class TestPrepareFeaturesContract:
    def test_feature_names_match_matrix_after_dropna(self):
        df = pd.DataFrame({
            "a": [1.0, 2.0, 3.0, 4.0],
            "leer": [np.nan] * 4,          # komplett leer → wird gedroppt
            "target": ["x", "y", "x", "y"],
        })
        out, names = prepare_features(df, drop_cols=["target"])
        assert names == list(out.columns), \
            f"feature_names {names} ≠ Matrix-Spalten {list(out.columns)}"
        assert "leer" not in names, "all-NaN-Spalte darf nicht in feature_names sein"
        assert "target" not in names

    def test_contract_holds_without_empty_columns(self):
        df = pd.DataFrame({
            "a": [1.0, 2.0], "b": [3.0, 4.0], "target": ["x", "y"],
        })
        out, names = prepare_features(df, drop_cols=["target"])
        assert names == ["a", "b"] == list(out.columns)

    def test_no_drop_cols_keeps_numeric_columns(self):
        df = pd.DataFrame({"a": [1.0], "text": ["w"]})
        out, names = prepare_features(df)
        assert names == ["a"]
        assert out.shape == (1, 1)


class TestNaNTargetHandling:
    def test_nan_targets_dropped_not_trained(self):
        from src.analysis.ml_analysis import run_classification
        rng = np.random.default_rng(3)
        df = pd.DataFrame({
            "a": rng.normal(size=40),
            "ziel": ["x"] * 15 + ["y"] * 15 + [None] * 10,  # 10 Zeilen ohne Ziel
        })
        res = run_classification(df, "ziel")
        assert "error" not in res
        assert res["n_dropped_nan_targets"] == 10
        assert "nan" not in res["classes"] and set(res["classes"]) == {"x", "y"}

    def test_all_targets_nan_returns_error_or_empty(self):
        from src.analysis.ml_analysis import run_classification
        df = pd.DataFrame({"a": [1.0, 2.0], "ziel": [None, None]})
        res = run_classification(df, "ziel")
        assert "error" in res or res.get("n_dropped_nan_targets") == 2
