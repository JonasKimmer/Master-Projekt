"""Regressionstests für src/preprocessing/quality_checks.py (Review5 #3).

Zentrale Regression: die Plausibilitäts-Ranges dürfen EXAKT auf den
Kanal-Namen (bzw. dessen Punkt-Segment) matchen, nicht per Substring —
'hr' matcht sonst auch 'hrv' (RMSSD in ms) und 'threshold' (Bool-Flag)
und markiert korrekte Daten als fehlerhaft.
"""

from __future__ import annotations

from src.models.experiment_records import SensorStreamRecord
from src.preprocessing.quality_checks import check_stream


def _stream(channels: dict[str, list], n: int | None = None) -> SensorStreamRecord:
    n = n if n is not None else max(len(v) for v in channels.values())
    return SensorStreamRecord(source="s", modality="m",
                              timestamps=[float(i * 100) for i in range(n)],
                              channels=channels)


def _issues(report, channel: str) -> list[str]:
    ch = next(c for c in report.channels if c.channel == channel)
    return ch.issues


class TestPlausibilityExactMatching:
    """Bug: Substring-Matching lieferte False Positives für 'hr'/'eda'."""

    def test_hrv_rmssd_not_checked_against_hr_range(self):
        # RMSSD liegt typischerweise bei 20–100 ms — plausibel, aber < 30
        rep = check_stream("T", _stream({"hrv": [45.0, 25.0, 60.0]}))
        assert _issues(rep, "hrv") == [], \
            f"'hrv' wurde gegen die Herzfrequenz-Range geprüft: {_issues(rep, 'hrv')}"

    def test_threshold_flag_not_checked_against_hr_range(self):
        # 'threshold' enthält den Substring 'hr' — Bool-Flags sind 0/1
        rep = check_stream("T", _stream({"mythreshold": [0.0, 1.0, 0.0]}))
        assert _issues(rep, "mythreshold") == []

    def test_median_named_channel_not_checked_against_eda(self):
        # 'eda' als Substring von 'rolling_median' o. ä. — darf nicht ziehen
        rep = check_stream("T", _stream({"rolling_median": [12.0, 13.0, 14.0]}))
        assert _issues(rep, "rolling_median") == []

    def test_plain_hr_still_checked(self):
        # Gegenprobe: echter 'hr'-Kanal wird weiterhin geprüft
        rep = check_stream("T", _stream({"hr": [60.0, 250.0, 70.0]}))
        assert any("outside plausible range" in i for i in _issues(rep, "hr"))

    def test_prefixed_channel_leaf_still_checked(self):
        # Gegenprobe: 'gaze.LeftX' → Segment 'leftx' → Range greift weiter
        rep = check_stream("T", _stream({"gaze.LeftX": [0.5, 5.0, 0.6]}))
        assert any("outside plausible range" in i for i in _issues(rep, "gaze.LeftX"))

    def test_heart_rate_underscore_variant_still_checked(self):
        # 'heart_rate' (ohne Punkt) → normalisiert 'heartrate' → exakter Key
        rep = check_stream("T", _stream({"heart_rate": [60.0, 250.0, 70.0]}))
        assert any("outside plausible range" in i for i in _issues(rep, "heart_rate"))

    def test_shimmer_gsr_still_checked(self):
        # Gegenprobe: reale Fusion-Kanäle bleiben abgedeckt
        rep = check_stream("T", _stream({"shimmer.GsrKOhm": [5000.0, -1.0, 4999.0]}))
        assert any("outside plausible range" in i for i in _issues(rep, "shimmer.GsrKOhm"))

    def test_binary_validity_flag_not_plausibility_checked(self):
        # Gültigkeits-Flags (0/1) dürfen keine Range-Verletzung auslösen
        rep = check_stream("T", _stream({"gaze.LeftValidity": [0.0, 1.0, 0.0]}))
        assert _issues(rep, "gaze.LeftValidity") == []


class TestStreamBasics:
    """Basis-Abdeckung des bislang ungetesteten Moduls."""

    def test_empty_stream_flagged(self):
        rep = check_stream("T", SensorStreamRecord(
            source="s", modality="m", timestamps=[], channels={}))
        assert not rep.ok
        assert "Stream is empty" in rep.global_issues

    def test_duplicate_timestamps_flagged(self):
        rep = check_stream("T", SensorStreamRecord(
            source="s", modality="m",
            timestamps=[0.0, 100.0, 100.0],
            channels={"v": [1.0, 2.0, 3.0]}))
        assert rep.duplicate_timestamps == 1

    def test_large_gap_flagged(self):
        rep = check_stream("T", SensorStreamRecord(
            source="s", modality="m",
            timestamps=[0.0, 100.0, 9000.0],
            channels={"v": [1.0, 2.0, 3.0]}))
        assert rep.max_gap_ms == 8900.0
        assert any("sampling gap" in i.lower() for i in rep.global_issues)

    def test_missing_values_counted(self):
        rep = check_stream("T", _stream({"v": [1.0, None, 3.0]}))
        ch = next(c for c in rep.channels if c.channel == "v")
        assert ch.n_missing == 1
