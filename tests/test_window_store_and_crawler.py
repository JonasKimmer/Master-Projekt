"""Regressionstests für Window-Store (#6), UI-Definitionsladen (#5) und
Crawler-URL-Normalisierung (#10)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.experiment_records import WindowDefinition  # noqa: E402
from src.preprocessing.window_store import WindowDefinitionStore  # noqa: E402


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
