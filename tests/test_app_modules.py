"""Tests für bisher ungetestete App-Module: windowing, sensor_features,
web_features, website_loader, tabular_loader (Review10-Liste)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from src.feature_engineering.sensor_features import (
    compute_channel_features,
    compute_window_features,
)
from src.feature_engineering.web_features import (
    page_features,
    website_features,
)
from src.models.experiment_records import (
    EventRecord,
    EventType,
    Segment,
    SensorStreamRecord,
    TrialTimeline,
    WindowDefinition,
)
from src.preprocessing.windowing import generate_windows, slice_stream


def _stream(ts, channels):
    return SensorStreamRecord(source="s", modality="m",
                              timestamps=list(ts), channels=channels)


# ── windowing ────────────────────────────────────────────────────────────────

class TestGenerateWindows:
    def test_fixed_single_window_clamped_to_stream(self):
        s = _stream(range(0, 10_000, 100), {"v": [1.0] * 100})
        w = generate_windows(s, WindowDefinition("a", "fixed", 2_000.0))
        assert w == [(0.0, 2_000.0)]

    def test_fixed_beyond_stream_clamps_end(self):
        s = _stream([0.0, 100.0, 200.0], {"v": [1, 2, 3]})
        w = generate_windows(s, WindowDefinition("a", "fixed", 5_000.0))
        assert w == [(0.0, 200.0)]

    def test_fixed_empty_window_raises(self):
        s = _stream([0.0, 100.0], {"v": [1, 2]})
        with pytest.raises(ValueError, match="Leeres fixed-Fenster"):
            generate_windows(s, WindowDefinition("a", "fixed", 100.0,
                                                 offset_start_ms=5_000.0))

    def test_sliding_step_and_count(self):
        s = _stream(range(0, 10_000, 100), {"v": [1.0] * 100})
        w = generate_windows(s, WindowDefinition("a", "sliding", 2_000.0, step_ms=1_000.0))
        assert len(w) == 8  # t_max = 9900
        assert w[0] == (0.0, 2_000.0) and w[1] == (1_000.0, 3_000.0)
        assert w[-1] == (7_000.0, 9_000.0)

    def test_sliding_defaults_step_to_duration(self):
        s = _stream(range(0, 6_000, 100), {"v": [1.0] * 60})
        w = generate_windows(s, WindowDefinition("a", "sliding", 2_000.0))
        assert len(w) == 2  # t_max = 5900

    def test_task_mode_filters_label_domain_and_incomplete(self):
        tl = TrialTimeline(trial_id="T")
        ev = lambda t, et=EventType.TASK_START, d=None: EventRecord(
            t, et, "task:start", {"domain": d} if d else {})
        tl.segments = [
            Segment(label="task", segment_type="task", start_ms=0.0, end_ms=1_000.0,
                    start_event=ev(0.0, d="gaming"), domain="gaming"),
            Segment(label="task", segment_type="task", start_ms=2_000.0, end_ms=3_000.0,
                    start_event=ev(2_000.0, d="health"), domain="health"),
            Segment(label="task", segment_type="task", start_ms=4_000.0, end_ms=None,
                    start_event=ev(4_000.0)),                                              # unvollständig
            Segment(label="baseline", segment_type="baseline", start_ms=5.0, end_ms=10.0,
                    start_event=ev(5.0, EventType.BASELINE_START)),                        # falsches Label
        ]
        s = _stream(range(0, 10_000, 100), {"v": [1.0] * 100})
        w = generate_windows(s, WindowDefinition("a", "task", 0.0, task_label="task",
                                                 task_domain="gaming"), timeline=tl)
        assert w == [(0.0, 1_000.0)]
        # ohne Domain-Filter: beide vollständigen Task-Segmente
        w2 = generate_windows(s, WindowDefinition("a", "task", 0.0, task_label="task"), timeline=tl)
        assert len(w2) == 2

    def test_task_mode_without_timeline_empty(self):
        s = _stream([0.0, 100.0], {"v": [1, 2]})
        assert generate_windows(s, WindowDefinition("a", "task", 0.0, task_label="t")) == []

    def test_empty_stream_returns_empty(self):
        s = _stream([], {})
        assert generate_windows(s, WindowDefinition("a", "fixed", 100.0)) == []


class TestSliceStream:
    def test_slice_inclusive_bounds(self):
        s = _stream(range(0, 1_000, 100), {"v": list(range(10))})
        out = slice_stream(s, 200.0, 500.0)
        assert out["timestamps"] == [200.0, 300.0, 400.0, 500.0]
        assert out["v"] == [2, 3, 4, 5]

    def test_slice_short_channel_safe(self):
        # Verletzte Invariante (Kanal kürzer als Timestamps) darf nicht crashen
        s = _stream(range(0, 500, 100), {"v": [1, 2, 3, 4, 5], "w": [1.0]})
        out = slice_stream(s, 0.0, 400.0)
        assert len(out["w"]) <= 1  # nur Indizes < len(values) übernehmen


# ── sensor_features ──────────────────────────────────────────────────────────

class TestComputeChannelFeatures:
    def test_basic_statistics(self):
        f = compute_channel_features([1.0, 2.0, 3.0, 4.0])
        assert f["mean"] == 2.5 and f["min"] == 1.0 and f["max"] == 4.0
        assert f["range"] == 3.0 and f["n_samples"] == 4.0
        assert f["variance"] == pytest.approx(f["std"] ** 2, rel=1e-6)

    def test_none_and_garbage_filtered(self):
        f = compute_channel_features([1.0, None, "x", 3.0, float("nan")])
        assert f["n_samples"] == 2.0 and f["mean"] == 2.0

    def test_all_invalid_returns_missing_rate_only(self):
        # Vertrag seit AP7-Fehlerrate: Kanäle ohne gültige Werte bleiben
        # sichtbar (missing_rate=1.0), statt als leeres Dict zu verschwinden
        assert compute_channel_features([None, "abc"]) == \
            {"missing_rate": 1.0, "n_samples": 0.0}

    def test_peak_count_and_trend(self):
        # Ein klarer Peak bei Index 1, steigender Trend 0,1,2,...,5
        vals = [0.0, 5.0, 1.0, 2.0, 3.0, 4.0]
        f = compute_channel_features(vals)
        assert f["peak_count"] == 1.0
        assert f["trend"] > 0

    def test_window_features_skips_timestamps(self):
        out = compute_window_features({"timestamps": [0.0, 1.0], "v": [1.0, 2.0]})
        assert "timestamps" not in out and "v" in out


# ── web_features ─────────────────────────────────────────────────────────────

def _page(pid, n_links=4, n_forms=1, n_media=2, text="Hallo " * 200, dom=None):
    from src.models.web_records import PageRecord
    return PageRecord(
        page_id=str(pid), source_dir=f"/x/{pid}", url=f"https://x/{pid}",
        visible_text={"url": f"https://x/{pid}", "text": text},
        links=[{"href": f"https://x/{i}"} for i in range(n_links)],
        forms=[{"action": ""} for _ in range(n_forms)],
        media=[{"type": "img"} for _ in range(n_media)],
        dom=dom if dom is not None else {"tag": "html", "children": [{"tag": "body"}]},
    )


class TestWebFeatures:
    def test_page_features_flat_dict(self):
        f = page_features(_page(1, n_links=4))
        assert f["link_count"] == 4 and f["form_count"] == 1 and f["media_count"] == 2
        assert f["text_length"] == len("Hallo " * 200)
        assert f["dom_nodes"] == 2 and f["dom_depth"] == 1
        assert f["has_screenshot"] == 0

    def test_dom_helpers_count_depth_and_nodes(self):
        from src.feature_engineering.web_features import _dom_depth, _dom_node_count
        dom = {"tag": "html", "children": [
            {"tag": "body", "children": [
                {"tag": "div", "children": []},
                {"tag": "p"},
            ]},
        ]}
        assert _dom_depth(dom) == 2
        assert _dom_node_count(dom) == 4

    def test_website_features_aggregates(self):
        from src.models.web_records import WebsiteRecord
        w = WebsiteRecord(website_id="W", source_dir="/x",
                          pages=[_page(1, n_links=4), _page(2, n_links=8)])
        agg = website_features(w)
        assert agg["page_count"] == 2
        assert agg["link_count_mean"] == 6.0
        assert agg["link_count_max"] == 8
        assert agg["text_length_sum"] == 2 * len("Hallo " * 200)


# ── website_loader ───────────────────────────────────────────────────────────

class TestWebsiteLoader:
    def _make_site(self, root: Path, n_pages=2):
        pages = root / "W" / "pages"
        for i in range(1, n_pages + 1):
            d = pages / str(i)
            d.mkdir(parents=True)
            (d / "visible_text.json").write_text(
                json.dumps({"url": f"https://w/{i}", "text": "Hallo Welt " * (i * 10)}),
                encoding="utf-8")
            (d / "links.json").write_text(
                json.dumps([{"href": f"https://w/{j}", "text": "l"} for j in range(i + 3)]),
                encoding="utf-8")
            (d / "dom.json").write_text(
                json.dumps({"tag": "html", "children": [{"tag": "body"}]}), encoding="utf-8")
        (root / "W" / "portal_meta.json").write_text(
            json.dumps({"start_url": "https://w", "page_count": n_pages}), encoding="utf-8")

    def test_load_websites_and_pages(self, tmp_path):
        self._make_site(tmp_path)
        sites = __import__("src.loaders.website_loader", fromlist=["load_websites_from_dir"]) \
            .load_websites_from_dir(str(tmp_path))
        assert len(sites) == 1
        site = sites[0]
        assert site.page_count == 2 and len(site.pages) == 2
        p1 = next(p for p in site.pages if p.page_id == "1")
        f = page_features(p1)
        assert f["link_count"] == 4 and f["text_length"] > 0 and f["dom_depth"] >= 1

    def test_corrupt_json_flagged_not_silent(self, tmp_path):
        # Korruptes Artefakt wird als Fehler vermerkt statt still als 0 durchzugehen
        self._make_site(tmp_path)
        (tmp_path / "W" / "pages" / "1" / "links.json").write_text("{kaputt", encoding="utf-8")
        sites = __import__("src.loaders.website_loader", fromlist=["load_websites_from_dir"]) \
            .load_websites_from_dir(str(tmp_path))
        p1 = next(p for p in sites[0].pages if p.page_id == "1")
        assert p1.load_errors == {"links.json": p1.load_errors["links.json"]}
        assert "JSONDecodeError" in p1.load_errors["links.json"]
        from src.feature_engineering.web_features import page_features
        assert page_features(p1)["link_count"] == 0  # Wert bleibt 0, aber ausgewiesen

    def test_intact_site_has_no_load_errors(self, tmp_path):
        self._make_site(tmp_path)
        sites = __import__("src.loaders.website_loader", fromlist=["load_websites_from_dir"]) \
            .load_websites_from_dir(str(tmp_path))
        assert all(p.load_errors == {} for p in sites[0].pages)


# ── tabular_loader ───────────────────────────────────────────────────────────

class TestTabularLoader:
    def test_load_csv(self, tmp_path):
        import pandas as pd
        from src.loaders.tabular_loader import load_data
        f = tmp_path / "d.csv"
        f.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
        df = load_data(f)
        assert list(df.columns) == ["a", "b"] and len(df) == 2

    def test_is_json_file(self, tmp_path):
        from src.loaders.tabular_loader import is_json_file
        assert is_json_file(tmp_path / "x.json")
        assert not is_json_file(tmp_path / "x.csv")


class TestMissingRateFeature:
    """AP7-Fehlerrate: missing_rate pro Kanal und Fenster (Review-Final #1)."""

    def test_missing_rate_computed(self):
        from src.feature_engineering.sensor_features import compute_channel_features
        f = compute_channel_features([1.0, None, 2.0, None, None])
        assert f["n_samples"] == 2.0
        assert f["missing_rate"] == 0.6

    def test_all_missing_channel_stays_visible(self):
        from src.feature_engineering.sensor_features import compute_channel_features
        f = compute_channel_features([None, None, None])
        assert f == {"missing_rate": 1.0, "n_samples": 0.0}

    def test_empty_slice_returns_empty(self):
        from src.feature_engineering.sensor_features import compute_channel_features
        assert compute_channel_features([]) == {}


class TestImuEegPlausibility:
    """AP8: IMU- und EEG/OpenBCI-Plausibilitätsbereiche (Review-Final #3)."""

    def test_imu_channels_get_ranges(self):
        from src.preprocessing.quality_checks import _plausibility_for_channel
        for ch, lo, hi in [
            ("shimmer.AccX", -16.0, 16.0), ("shimmer.AccWrZ", -16.0, 16.0),
            ("shimmer.GyroY", -2000.0, 2000.0), ("shimmer.MagX", -400.0, 400.0),
            ("eeg", -4000.0, 4000.0), ("openbci.eeg3", -4000.0, 4000.0),
        ]:
            r = _plausibility_for_channel(ch)
            assert r == (lo, hi), f"{ch}: {r}"

    def test_imu_out_of_range_flagged(self):
        from src.models.experiment_records import SensorStreamRecord
        from src.preprocessing.quality_checks import check_stream
        s = SensorStreamRecord(source="t", modality="fusion",
                               timestamps=[0.0, 100.0, 200.0],
                               channels={"shimmer.AccX": [1.0, 99.0, 2.0]})
        rep = check_stream("T", s)
        issues = [i for c in rep.channels for i in c.issues]
        assert any("outside plausible" in i for i in issues)

    def test_real_data_imu_stays_in_range(self):
        # Gegenprobe auf echten Daten: normale IMU-Werte dürfen keine
        # Plausibilitäts-Issues erzeugen
        from src.loaders.trial_loader import load_trial
        from src.preprocessing.quality_checks import check_stream
        t = load_trial("data/T-1")
        rep = check_stream(t.trial_id, t.streams[0])
        imu = [c for c in rep.channels if c.channel.split(".")[-1]
               .lower().startswith(("acc", "gyro", "mag"))]
        assert imu, "IMU-Kanäle nicht gefunden"
        assert all(c.n_out_of_range == 0 for c in imu), \
            [(c.channel, c.n_out_of_range) for c in imu if c.n_out_of_range]


class TestSensorTab:
    """AP11: eigenständiger Sensoranalyse-Tab."""

    _APP = str(Path(__file__).resolve().parent.parent / "app.py")

    def test_app_has_nine_tabs_with_sensor(self, tmp_path, monkeypatch, synthetic_trial):
        from streamlit.testing.v1 import AppTest
        monkeypatch.chdir(tmp_path)
        at = AppTest.from_file(self._APP, default_timeout=120)
        at.session_state["trials"] = [synthetic_trial]
        at.run()
        assert not at.exception, f"{at.exception}"
        # AppTest flacht auch verschachtelte Innertabs des Trials-Tabs ab;
        # die oberste Ebene ergibt sich nach Entfernen der Innertab-Labels
        inner = {"Timeline", "Events", "Qualität", "Analysen"}
        labels = [t.label for t in at.tabs if t.label not in inner]
        assert labels == ["Tabellarische Daten", "Import", "Dateninventar",
                          "Trials", "Zeitfenster", "Sensoranalyse",
                          "Websites", "Reporting", "ML"]

    def test_sensor_tab_modality_quality(self, tmp_path, monkeypatch, synthetic_trial):
        from streamlit.testing.v1 import AppTest
        monkeypatch.chdir(tmp_path)
        at = AppTest.from_file(self._APP, default_timeout=120)
        at.session_state["trials"] = [synthetic_trial]
        at.run()
        # Beide Modalitäten anbieten, shimmer auswählen darf nicht crashen
        assert sorted(at.selectbox(key="sensor_modality").options) == \
            ["eye_tracking", "shimmer_physio"]
        at.selectbox(key="sensor_modality").set_value("shimmer_physio")
        at.run()
        assert not at.exception, f"{at.exception}"
