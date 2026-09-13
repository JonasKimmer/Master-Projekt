"""AP3/AP4: keine harte Bindung an exakte Dateinamen; sensor_loader."""

from __future__ import annotations

import json
from pathlib import Path

from src.loaders.sensor_loader import find_sensor_files, load_sensor_streams, parse_sensor_stream
from src.loaders.trial_loader import find_event_file, load_trial
from src.loaders.website_loader import load_website


def _write(path: Path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")


class TestTrialFilenames:
    def test_canonical_names_still_work(self, tmp_path):
        _write(tmp_path / "events.ndjson", [{"ts": 1, "type": "task:start"}])
        _write(tmp_path / "fusion_merged.ndjson", [{"ts": 1, "gaze": {"x": 0.5}}])
        t = load_trial(str(tmp_path))
        assert len(t.events) == 1 and len(t.streams) == 1

    def test_alternative_event_names(self, tmp_path):
        _write(tmp_path / "events.json", [{"ts": 1, "type": "task:start"}])
        assert find_event_file(tmp_path).name == "events.json"
        assert len(load_trial(str(tmp_path)).events) == 1

        # Kanonische Namen haben Vorrang vor Mustern …
        _write(tmp_path / "events_t1.ndjson", [{"ts": 2, "type": "task:end"}])
        assert find_event_file(tmp_path).name == "events.json"
        # … aber ohne kanonische Datei greift das Muster
        other = tmp_path / "only-pattern"
        _write(other / "events_t1.ndjson", [{"ts": 3, "type": "task:end"}])
        assert find_event_file(other).name == "events_t1.ndjson"
        assert len(load_trial(str(other)).events) == 1

    def test_alternative_sensor_names_and_modalities(self, tmp_path):
        _write(tmp_path / "fusion_merged.json", [{"ts": 1, "shimmer": {"GsrKOhm": 100.0}}])
        _write(tmp_path / "openbci_eeg.ndjson", [{"ts": 1, "channel_1": 12.5}])
        files = find_sensor_files(tmp_path)
        modalities = {p.name: m for p, m in files}
        assert modalities == {"fusion_merged.json": "fusion", "openbci_eeg.ndjson": "eeg"}
        streams = load_sensor_streams(tmp_path)
        assert [s.modality for s in streams] == ["fusion", "eeg"]
        assert "shimmer.GsrKOhm" in streams[0].channels
        assert "channel_1" in streams[1].channels

    def test_events_file_not_mistaken_for_sensor(self, tmp_path):
        _write(tmp_path / "events.ndjson", [{"ts": 1, "type": "x"}])
        assert find_sensor_files(tmp_path) == []

    def test_trial_recognition_via_patterns(self, tmp_path):
        trial = tmp_path / "t-1"
        _write(trial / "events_v2.ndjson", [{"ts": 1, "type": "task:start"}])
        trials = __import__("src.loaders.trial_loader", fromlist=["load_trials_from_dir"]).load_trials_from_dir(str(tmp_path))
        assert [t.trial_id for t in trials] == ["t-1"]


class TestWebsiteFilenames:
    def test_alternative_artifact_names(self, tmp_path):
        page = tmp_path / "1" / "pages" / "1"
        page.mkdir(parents=True)
        (page / "Links.json").write_text(json.dumps([{"href": "https://x"}]), encoding="utf-8")
        (page / "dom_v2.json").write_text(json.dumps({"tag": "html"}), encoding="utf-8")
        w = load_website(str(tmp_path / "1"))
        assert w.pages[0].link_count == 1
        assert w.pages[0].dom == {"tag": "html"}
