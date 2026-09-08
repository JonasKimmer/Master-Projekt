"""Regressionstests für die Tabular-UI-Filter (Review5 #1, #2).

  1. Globale Textsuche darf bei Regex-Sonderzeichen nicht crashen
  2. All-NaN-numerische Spalten dürfen keinen NaN-Slider bauen
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_tabular(df: pd.DataFrame):
    """app.py mit injiziertem Tabular-DataFrame ausführen (echter Widget-Pfad
    inkl. Sidebar-Filter, wie bei echtem Upload über set_tabular)."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
    at.session_state["tabular_df"] = df
    at.session_state["tabular_raw_json"] = None
    at.session_state["tabular_record"] = None
    at.run()
    return at


def _search_input(at):
    return next(t for t in at.sidebar.text_input
                if t.label.startswith("Globale Textsuche"))


def _filter_select(at):
    return next(m for m in at.sidebar.multiselect
                if m.label.startswith("Spalten für Filter"))


class TestTextSearchRegexSafe:
    """Bug: str.contains lief mit regex=True — '(' crashte die ganze Ansicht."""

    def test_regex_special_chars_do_not_crash(self):
        df = pd.DataFrame({"text": ["alpha (v1)", "beta [x]", "gamma"]})
        at = _run_tabular(df)
        assert not at.exception
        _search_input(at).set_value("(v1")  # unbalancierte Klammer
        at.run()
        assert not at.exception, \
            f"Textsuche mit Regex-Sonderzeichen crashte: {at.exception}"

    def test_brackets_and_pipes_do_not_crash(self):
        df = pd.DataFrame({"text": ["a", "b"]})
        at = _run_tabular(df)
        for term in ("[abc]", "a|b", "(", "*", "+?"):
            _search_input(at).set_value(term)
            at.run()
            assert not at.exception, f"Suchterm {term!r} crashte: {at.exception}"

    def test_literal_search_still_matches(self):
        # Gegenprobe: normales Suchen funktioniert weiterhin (kein Fehler-
        # wohlergehen durch stummes Abschalten der Suche)
        df = pd.DataFrame({"text": ["Apfel", "Birne"]})
        at = _run_tabular(df)
        _search_input(at).set_value("apf")  # case-insensitive
        at.run()
        assert not at.exception


class TestNumericSliderNanGuard:
    """Bug: all-NaN-Spalte → min=max=nan, nan != nan ist True → Slider
    mit min_value=nan crashte beim Auswählen der Spalte im Filter."""

    def test_all_nan_numeric_column_no_slider_crash(self):
        # Achtung: Streamlit crasht dabei nicht, sondern baut einen
        # defekten Slider mit min=max=nan. Der Defekt ist die Existenz
        # dieses Sliders, nicht eine Exception.
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "leer": [np.nan] * 3})
        assert pd.api.types.is_numeric_dtype(df["leer"]), \
            "Test-Setup: Spalte muss numerisch sein, um den Slider-Zweig zu treffen"
        at = _run_tabular(df)
        _filter_select(at).set_value(["leer"])
        at.run()
        assert not at.exception, f"NaN-Slider-Crash: {at.exception}"
        broken = [s for s in at.sidebar.slider if s.label == "Wertebereich leer"]
        assert not broken, \
            f"All-NaN-Spalte erzeugt defekten NaN-Slider: {[(s.min, s.max) for s in broken]}"

    def test_partially_nan_column_slider_still_works(self):
        # Gegenprobe: teils NaN → min/max fallen NaN heraus, Slider bleibt
        df = pd.DataFrame({"x": [1.0, np.nan, 5.0]})
        at = _run_tabular(df)
        _filter_select(at).set_value(["x"])
        at.run()
        assert not at.exception
        ok = [s for s in at.sidebar.slider if s.label == "Wertebereich x"]
        assert ok and ok[0].min == 1.0 and ok[0].max == 5.0, \
            "Slider für teils-NaN-Spalte fehlt oder hat falsche Grenzen"

    def test_constant_column_skips_slider(self):
        # Gegenprobe: min == max → kein Slider (bereits vorher so)
        df = pd.DataFrame({"x": [2.0, 2.0, 2.0], "y": [1.0, 2.0, 3.0]})
        at = _run_tabular(df)
        _filter_select(at).set_value(["x", "y"])
        at.run()
        assert not at.exception
        labels = [s.label for s in at.sidebar.slider]
        assert "Wertebereich x" not in labels, "konstante Spalte darf keinen Slider bauen"
        assert "Wertebereich y" in labels, "variable Spalte muss einen Slider bauen"
