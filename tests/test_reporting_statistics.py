"""Tests für die letzten ungetesteten Analyse- und Exportpfade:
src/analysis/statistics.notable_windows und src/analysis/reporting."""

from __future__ import annotations

import pandas as pd

from src.analysis.reporting import (
    df_to_csv_bytes,
    str_to_bytes,
    timeline_to_dataframe,
    trial_markdown_report,
    website_markdown_report,
    window_features_to_dataframe,
)
from src.analysis.statistics import notable_windows
from src.models.experiment_records import (
    EventRecord,
    EventType,
    Segment,
    TrialTimeline,
    WindowFeatureRecord,
)
from src.models.web_records import PageRecord, WebsiteRecord


def _timeline():
    tl = TrialTimeline(trial_id="T1")
    ev = EventRecord(0.0, EventType.TASK_START, "task:start", {"domain": "gaming"})
    tl.segments = [
        Segment(label="task", segment_type="task", start_ms=0.0, end_ms=1000.0,
                start_event=ev, domain="gaming"),
    ]
    return tl


class TestNotableWindows:
    def _df(self):
        # Ein Kanal, 6 Fenster: Fenster 3 hat Extremwerte, Fenster 5 zu wenig Samples
        return pd.DataFrame({
            "window":  list(range(6)),
            "start_ms": [i * 1000 for i in range(6)],
            "end_ms":   [(i + 1) * 1000 for i in range(6)],
            "channel":  "v",
            "mean":     [10.0, 10.0, 10.0, 100.0, 10.0, 10.0],   # Fenster 3: Ausreißer
            "std":      [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            "n_samples": [20, 20, 20, 20, 20, 2],                 # Fenster 5: 2 < min 5
        })

    def test_outlier_mean_flagged_with_reason(self):
        flagged = notable_windows(self._df())
        assert 3 in set(flagged["window"])
        row = flagged[flagged["window"] == 3].iloc[0]
        assert "mean z=" in row["reason"]

    def test_low_sample_count_flagged(self):
        flagged = notable_windows(self._df())
        assert 5 in set(flagged["window"])
        assert "2 Samples" in flagged[flagged["window"] == 5].iloc[0]["reason"]

    def test_normal_windows_not_flagged(self):
        flagged = notable_windows(self._df())
        assert set(flagged["window"]) == {3, 5}

    def test_empty_or_missing_channel_returns_empty(self):
        assert notable_windows(pd.DataFrame()).empty
        assert notable_windows(pd.DataFrame({"mean": [1.0]})).empty


class TestReporting:
    def test_timeline_to_dataframe_rows(self):
        df = timeline_to_dataframe(_timeline())
        assert len(df) == 1
        assert df.iloc[0]["label"] == "task"

    def test_window_features_wide_format(self):
        recs = [WindowFeatureRecord(window_id="w", trial_id="T", modality="m",
                                    start_ms=0.0, end_ms=100.0,
                                    features={"v": {"mean": 1.0, "std": 0.1}})]
        df = window_features_to_dataframe(recs)
        assert "v_mean" in df.columns and df.iloc[0]["v_mean"] == 1.0

    def test_markdown_reports_contain_core_facts(self):
        tl = _timeline()
        tl.quality_issues.append("Test-Issue")
        md = trial_markdown_report(tl)
        assert "T1" in md and "task" in md
        site = WebsiteRecord(website_id="W", source_dir="/w", pages=[
            PageRecord(page_id="1", source_dir="/w/1", url="https://w/1",
                       links=[{"href": "https://x"}]),
        ])
        assert "W" in website_markdown_report(site)

    def test_bytes_helpers(self):
        df = pd.DataFrame({"a": [1, 2]})
        assert df_to_csv_bytes(df).splitlines()[0].strip() == b"a"
        assert str_to_bytes("x") == b"x"
