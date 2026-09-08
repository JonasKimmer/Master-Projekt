"""Regressionstests für src/preprocessing/synchronization.py.

Deckt die Review-Befunde 1, 2 und 4 ab:
  1. synchronize_streams muss ein GEMEINSAMES Raster erzeugen
  2. echte Messpunkte an Lückengrenzen dürfen nicht zu None werden
  4. unsortierte Timestamps müssen abgesichert sein (np.interp/searchsorted)
"""

from __future__ import annotations

import pytest

from src.models.experiment_records import SensorStreamRecord
from src.preprocessing.synchronization import (
    resample_stream,
    synchronize_streams,
    synchronize_trial,
)

from conftest import make_trial


def _stream(timestamps, channels, source="s", modality="m"):
    return SensorStreamRecord(source=source, modality=modality,
                              timestamps=list(timestamps), channels=channels)


class TestSharedGrid:
    """Bug 1: gemeinsames Zeitraster über Streams mit verschiedenen Startzeiten."""

    def test_earliest_gives_identical_timestamps(self):
        a = _stream([100.0, 200.0], {"x": [1.0, 2.0]}, source="a")
        b = _stream([150.0, 350.0], {"y": [3.0, 4.0]}, source="b")
        sa, sb = synchronize_streams([a, b], 10.0, base="earliest")
        assert sa.timestamps == sb.timestamps, "Streams müssen dasselbe Raster tragen"
        assert sa.timestamps[0] == 100.0        # früher Start beider
        assert sa.timestamps[-1] == 300.0       # gemeinsames Raster bis 300
        assert len(sa.timestamps) == 3          # 100, 200, 300

    def test_latest_trims_to_common_overlap(self):
        a = _stream([100.0, 300.0], {"x": [1.0, 2.0]})
        b = _stream([150.0, 450.0], {"y": [3.0, 4.0]})
        sa, sb = synchronize_streams([a, b], 10.0, base="latest")
        assert sa.timestamps == sb.timestamps
        assert sa.timestamps == [150.0, 250.0]  # spätester Start, frühestes Ende

    def test_values_outside_own_range_are_none_but_grid_shared(self):
        # Stream b misst nur ab 150 — vor 150 muss None stehen, Raster gleich
        a = _stream([100.0, 200.0], {"x": [1.0, 2.0]})
        b = _stream([150.0, 200.0], {"y": [3.0, 4.0]})
        sa, sb = synchronize_streams([a, b], 10.0, base="earliest")
        assert sa.timestamps == sb.timestamps
        i_100 = sb.timestamps.index(100.0)
        assert sb.channels["y"][i_100] is None  # keine Extrapolation
        i_200 = sb.timestamps.index(200.0)
        assert sb.channels["y"][i_200] == 4.0   # echte Messung bleibt

    def test_latest_without_overlap_raises(self):
        a = _stream([0.0, 100.0], {"x": [1.0, 2.0]})
        b = _stream([500.0, 600.0], {"y": [3.0, 4.0]})
        with pytest.raises(ValueError, match="Überlappung"):
            synchronize_streams([a, b], 10.0, base="latest")

    def test_synchronize_trial_modalities_share_grid(self, synthetic_trial):
        parts = synchronize_trial(synthetic_trial, 10.0)
        assert len(parts) == 2
        assert parts[0].timestamps == parts[1].timestamps


class TestGapBoundaries:
    """Bug 2: echte Messpunkte an Lückengrenzen müssen erhalten bleiben."""

    def test_real_measurements_at_gap_edges_survive(self):
        s = _stream([0.0, 100.0, 10000.0, 10100.0], {"v": [0.0, 1.0, 10.0, 11.0]})
        r = resample_stream(s, 10.0)
        by_t = {round(t): v for t, v in zip(r.timestamps, r.channels["v"])}
        assert by_t[0] == 0.0
        assert by_t[100] == 1.0
        assert by_t[10000] == 10.0, "Messpunkt an Lückengrenze darf nicht None werden"
        assert by_t[10100] == 11.0

    def test_far_inside_large_gap_is_none(self):
        # Mitten in der 9900-ms-Lücke darf kein interpolierter Wert stehen
        s = _stream([0.0, 100.0, 10000.0, 10100.0], {"v": [0.0, 1.0, 10.0, 11.0]})
        r = resample_stream(s, 10.0)
        deep = [v for t, v in zip(r.timestamps, r.channels["v"]) if 500 <= t <= 9500]
        assert all(v is None for v in deep), "Interpolation über große Lücke hinweg"

    def test_grid_size_guard(self):
        s = _stream([0.0, 86_400_000.0], {"v": [1.0, 2.0]})  # 24 h Spanne
        with pytest.raises(ValueError, match="Rasterpunkte"):
            resample_stream(s, 1000.0)


class TestUnsortedTimestamps:
    """Bug 4: unsortierte Timestamps müssen korrekt verarbeitet werden."""

    def test_unsorted_stream_resamples_correctly(self):
        # Identische Daten wie sortiert, nur die Zeilenreihenfolge verdreht
        sorted_s = _stream([0.0, 100.0, 200.0, 300.0], {"v": [0.0, 1.0, 2.0, 3.0]})
        unsorted_s = _stream([200.0, 0.0, 300.0, 100.0],
                             {"v": [2.0, 0.0, 3.0, 1.0]})
        r_sorted = resample_stream(sorted_s, 10.0)
        r_unsorted = resample_stream(unsorted_s, 10.0)
        assert r_unsorted.timestamps == r_sorted.timestamps
        assert r_unsorted.channels["v"] == r_sorted.channels["v"]

    def test_unsorted_with_gap_boundary(self):
        s = _stream([10000.0, 0.0, 10100.0, 100.0], {"v": [10.0, 0.0, 11.0, 1.0]})
        r = resample_stream(s, 10.0)
        by_t = {round(t): v for t, v in zip(r.timestamps, r.channels["v"])}
        assert by_t[0] == 0.0 and by_t[100] == 1.0
        assert by_t[10000] == 10.0 and by_t[10100] == 11.0
