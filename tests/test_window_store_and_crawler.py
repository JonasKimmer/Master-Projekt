"""Regressionstests für Window-Store (#6), UI-Definitionsladen (#5) und
Crawler-URL-Normalisierung (#10)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.experiment_records import (  # noqa: E402
    EventRecord,
    EventType,
    TrialRecord,
    WindowDefinition,
)
from src.preprocessing.window_store import WindowDefinitionStore  # noqa: E402

from conftest import make_fusion_stream, make_trial  # noqa: E402


class TestWindowStoreVersioning:
    """Bug 6: Namen mit Leerzeichen dürfen keine doppelte Version 1 erzeugen."""

    def test_whitespace_names_share_version_history(self, tmp_path):
        store = WindowDefinitionStore(tmp_path / "defs.json")
        e1 = store.save("baseline", WindowDefinition("a", "sliding", 1000.0))
        e2 = store.save("  baseline ", WindowDefinition("a", "sliding", 2000.0))
        e3 = store.save("\tbaseline\n", WindowDefinition("a", "sliding", 3000.0))
        assert (e1["version"], e2["version"], e3["version"]) == (1, 2, 3), \
            "ungetrimmter Name hat eine zweite Version 1 erzeugt"

    def test_list_entries_filters_trimmed(self, tmp_path):
        store = WindowDefinitionStore(tmp_path / "defs.json")
        store.save("a", WindowDefinition("a", "sliding", 1000.0))
        store.save("b", WindowDefinition("b", "sliding", 1000.0))
        assert len(store.list_entries(" a ")) == 1
        assert len(store.list_entries()) == 2

    def test_roundtrip_with_task_domain(self, tmp_path):
        store = WindowDefinitionStore(tmp_path / "defs.json")
        wd = WindowDefinition("t", "task", 0.0, task_label="task",
                              task_domain="gaming", offset_start_ms=100.0)
        entry = store.save("task_gaming", wd)
        loaded = store.load(entry["id"])
        assert loaded == wd

    def test_empty_name_rejected(self, tmp_path):
        store = WindowDefinitionStore(tmp_path / "defs.json")
        with pytest.raises(ValueError):
            store.save("   ", WindowDefinition("x", "sliding", 1000.0))


class TestCrawlerUrlNormalization:
    """Bug 10: URL-Dedup muss Fragment und Query-Reihenfolge normalisieren."""

    @classmethod
    def setup_class(cls):
        sys.path.insert(0, str(PROJECT_ROOT))
        import mini_crawler
        # staticmethod, sonst wird die Modulfunktion zur gebundenen Methode
        cls.normalize_url = staticmethod(mini_crawler.normalize_url)

    def test_fragment_stripped(self):
        assert self.normalize_url("https://x.de/a#section") == "https://x.de/a"

    def test_query_order_normalized(self):
        assert (self.normalize_url("https://x.de/p?a=1&b=2")
                == self.normalize_url("https://x.de/p?b=2&a=1"))

    def test_empty_path_normalized_to_root(self):
        assert self.normalize_url("https://x.de") == self.normalize_url("https://x.de/")

    def test_different_query_still_distinct(self):
        assert (self.normalize_url("https://x.de/p?a=1")
                != self.normalize_url("https://x.de/p?a=2"))

    def test_dedup_repro(self):
        # Vorher: Check gegen 'href' (mit Fragment), Append von 'clean' —
        # dadurch konnten Duplikate in die Queue kommen. Erwartung: 3
        # eindeutige Ziele (/a, /a?a=1&b=2 — Query macht es eine andere
        # Ressource — und /b); Fragment- und Query-Reihenfolge-Varianten
        # fallen alle auf dieselbe kanonische Form zusammen.
        urls = [
            "https://x.de/a",
            "https://x.de/a#top",
            "https://x.de/a?b=2&a=1",
            "https://x.de/a?a=1&b=2#top",
            "https://x.de/b",
        ]
        seen, queue = set(), []
        for u in urls:
            n = self.normalize_url(u)
            if n not in seen and n not in queue:
                queue.append(n)
                seen.add(n)
        assert len(queue) == 3
        assert queue[0] == "https://x.de/a"
        assert queue[1] == "https://x.de/a?a=1&b=2"


class TestWindowsTabLoadDefinition:
    """Bug 5: Laden gespeicherter Definitionen darf keine
    StreamlitAPIException auslösen und muss die Werte anwenden."""

    def test_save_and_load_via_app(self, tmp_path, monkeypatch, synthetic_trial):
        monkeypatch.chdir(tmp_path)  # window_definitions.json ins tmp_dir
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
        at.session_state["trials"] = [synthetic_trial]
        at.run()
        assert not at.exception

        # Konfiguration ändern, benannt speichern
        at.radio(key="win_mode").set_value("fixed")
        at.number_input(key="win_duration").set_value(5000)
        at.text_input(key="win_def_name").set_value("testdef")
        at.run()
        at.button(key="win_def_save").click()
        at.run()
        assert not at.exception
        assert (tmp_path / "window_definitions.json").exists()

        # Widgets bewusst verändern, dann gespeicherte Definition laden
        at.radio(key="win_mode").set_value("sliding")
        at.number_input(key="win_duration").set_value(2000)
        at.run()
        at.button(key="win_def_load").click()
        at.run()
        assert not at.exception, \
            f"Laden löste Exception aus: {at.exception}"
        assert at.radio(key="win_mode").value == "fixed"
        assert at.number_input(key="win_duration").value == 5000

    def test_loading_non_task_definition_clears_stale_task_label(
        self, tmp_path, monkeypatch, synthetic_trial
    ):
        """Review2 #6: eine Fixed-/Sliding-Definition muss eine vorherige
        Task-Auswahl zurücksetzen, sonst klebt sie im UI-State fest."""
        monkeypatch.chdir(tmp_path)
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
        at.session_state["trials"] = [synthetic_trial]
        at.run()

        # Task-Modus wählen → win_task_label wird gebunden und gesetzt
        at.radio(key="win_mode").set_value("task")
        at.run()
        assert not at.exception
        assert "win_task_label" in at.session_state

        # Fixed-Definition speichern und laden
        at.radio(key="win_mode").set_value("fixed")
        at.text_input(key="win_def_name").set_value("fixeddef")
        at.run()
        at.button(key="win_def_save").click()
        at.run()
        at.button(key="win_def_load").click()
        at.run()
        assert not at.exception
        assert "win_task_label" not in at.session_state, \
            "Veraltete Task-Auswahl blieb nach Laden einer Fixed-Definition im State"

    def test_loading_task_definition_with_unknown_label_resets(
        self, tmp_path, monkeypatch, synthetic_trial
    ):
        """Review2 #6: Task-Definition, deren Label im Trial nicht existiert,
        darf nicht crashen und muss die Auswahl zurücksetzen."""
        monkeypatch.chdir(tmp_path)
        import json as _json
        # Store-Datei direkt mit einer Task-Definition für ein unbekanntes
        # Label/Domain anlegen
        (tmp_path / "window_definitions.json").write_text(_json.dumps({
            "next_id": 2,
            "definitions": [{
                "id": 1, "name": "ghost", "version": 1,
                "created_at": "2026-09-08T12:00:00",
                "params": {"window_id": "ghost", "mode": "task", "duration_ms": 1000.0,
                           "step_ms": None, "task_label": "task",
                           "task_domain": "does-not-exist",
                           "offset_start_ms": 0.0, "offset_end_ms": 0.0, "meta": {}},
            }],
        }), encoding="utf-8")

        from streamlit.testing.v1 import AppTest
        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
        at.session_state["trials"] = [synthetic_trial]
        at.run()
        assert not at.exception

        at.button(key="win_def_load").click()  # einzige Definition auswählen & laden
        at.run()
        assert not at.exception, f"Unbekanntes Task-Label crashte die App: {at.exception}"
        assert at.radio(key="win_mode").value == "task"
        # Selectbox muss einen gültigen Wert zeigen (nicht das Geister-Label)
        valid = {"task [gaming]", "task [health]", "baseline"}
        assert at.selectbox(key="win_task_label").value in valid


class TestTrialSwitchResetsTaskLabel:
    """Review3 #2: beim Wechsel von Trial A zu Trial B muss die Task-Auswahl
    zurückgesetzt werden — nicht nur beim Laden gespeicherter Definitionen.
    Das Label von A kann für B ungültig oder schlicht falsch sein."""

    def _trial_b(self) -> TrialRecord:
        # T-B teilt EIN Label mit T-SYN ('task [gaming]') und hat ein
        # eigenes ('task [city]'). Genau bei solchen Overlaps bleibt eine
        # stale Auswahl unauffällig gültig — Streamlit resettet nur Werte,
        # die in den Optionen des neuen Trials gar nicht existieren.
        events = [
            EventRecord(0.0, EventType.BASELINE_START, "baseline:start", {}),
            EventRecord(500.0, EventType.BASELINE_END, "baseline:end", {}),
            EventRecord(600.0, EventType.TASK_START, "task:start",
                        {"domain": "city"}),
            EventRecord(1400.0, EventType.TASK_END, "task:end",
                        {"domain": "city"}),
            EventRecord(1500.0, EventType.TASK_START, "task:start",
                        {"domain": "gaming"}),
            EventRecord(2900.0, EventType.TASK_END, "task:end",
                        {"domain": "gaming"}),
        ]
        return TrialRecord("T-B", "/syn", events=events,
                           streams=[make_fusion_stream()])

    def test_switching_trial_resets_stale_task_selection(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
        at.session_state["trials"] = [make_trial(), self._trial_b()]
        at.run()
        assert not at.exception

        # Task-Modus aktivieren und bewusst ein Label von Trial A wählen
        at.radio(key="win_mode").set_value("task")
        at.run()
        at.selectbox(key="win_task_label").set_value("task [gaming]")
        at.run()
        assert at.selectbox(key="win_task_label").value == "task [gaming]"

        # Trial wechseln — die Auswahl von A darf nicht kleben bleiben,
        # auch wenn 'task [gaming]' in T-B ebenfalls existiert
        at.selectbox(key="win_trial").set_value("T-B")
        at.run()
        assert not at.exception, f"Trial-Wechsel crashte die App: {at.exception}"
        stale = at.session_state["win_task_label"]
        assert stale != "task [gaming]", \
            f"Stale Task-Label von Trial A blieb im Session-State: {stale!r}"
        assert at.selectbox(key="win_task_label").value == stale

    def test_switching_trial_with_disjoint_labels_shows_valid_default(
        self, tmp_path, monkeypatch
    ):
        # Labels von T-B existieren in T-A gar nicht: Auswahl muss auf
        # einen gültigen Default von T-B fallen (kein Crash, kein Ghost).
        monkeypatch.chdir(tmp_path)
        from streamlit.testing.v1 import AppTest

        trial_b = TrialRecord("T-B", "/syn", events=[
            EventRecord(0.0, EventType.BASELINE_START, "baseline:start", {}),
            EventRecord(900.0, EventType.BASELINE_END, "baseline:end", {}),
        ], streams=[make_fusion_stream()])

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
        at.session_state["trials"] = [make_trial(), trial_b]
        at.run()
        at.radio(key="win_mode").set_value("task")
        at.run()
        at.selectbox(key="win_task_label").set_value("task [health]")
        at.run()

        at.selectbox(key="win_trial").set_value("T-B")
        at.run()
        assert not at.exception, f"Trial-Wechsel crashte die App: {at.exception}"
        assert at.session_state["win_task_label"] == "baseline"
        assert at.selectbox(key="win_task_label").value == "baseline"

    def test_selection_survives_reruns_within_same_trial(
        self, tmp_path, monkeypatch
    ):
        # Gegenprobe: innerhalb desselben Trials darf der Reset die
        # manuelle Auswahl nicht bei jedem Rerun wegwerfen.
        monkeypatch.chdir(tmp_path)
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=120)
        at.session_state["trials"] = [make_trial()]
        at.run()
        at.radio(key="win_mode").set_value("task")
        at.run()
        at.selectbox(key="win_task_label").set_value("task [health]")
        at.run()
        at.run()  # erneuter Rerun ohne Interaktion
        assert at.selectbox(key="win_task_label").value == "task [health]", \
            "Auswahl wurde innerhalb desselben Trials zurückgesetzt"
