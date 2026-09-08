"""Regressionstest: Missing-Value-Report mit NaN in der Gruppenspalte.

Bug (Breit-Durchsicht Runde 1, nie behoben): groupby(group_col).apply()
verwirft unter pandas 3 die NaN-Zeilen UND die Gruppenspalte aus dem
Ergebnis; die anschließende Indizierung missing_rates[missing>0].index
crashte dann mit KeyError, sobald die Gruppenspalte selbst fehlende
Werte hatte.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_with_df(df: pd.DataFrame):
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
    at.session_state["tabular_df"] = df
    at.session_state["tabular_raw_json"] = None
    at.session_state["tabular_record"] = None
    at.run()
    return at


class TestMissingValueReport:
    def test_nan_in_group_column_does_not_crash(self):
        df = pd.DataFrame({
            "gruppe": ["A", "A", None, "B"],      # NaN in der Gruppenspalte
            "wert": [1.0, np.nan, 3.0, 4.0],      # NaN in der Wertspalte
        })
        at = _run_with_df(df)
        btn = next(b for b in at.button if "Missing-Value-Report" in b.label)
        btn.click()
        at.run()
        assert not at.exception, \
            f"Missing-Value-Report crashte bei NaN in der Gruppenspalte: {at.exception}"

    def test_report_without_group_nan_still_works(self):
        # Gegenprobe: klassischer Fall bleibt funktionsfähig
        df = pd.DataFrame({"gruppe": ["A", "A", "B"], "wert": [1.0, np.nan, 3.0]})
        at = _run_with_df(df)
        btn = next(b for b in at.button if "Missing-Value-Report" in b.label)
        btn.click()
        at.run()
        assert not at.exception
