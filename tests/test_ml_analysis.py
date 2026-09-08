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
