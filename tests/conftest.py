"""Gemeinsame Test-Fixtures.

Stellt sicher, dass `src` importierbar ist (unabhängig vom Aufrufverzeichnis)
und bietet synthetische Trials/Streams, damit die Test-Suite NICHT von den
lokalen, git-ignorierten data/-Projektdaten abhängt — sie läuft deshalb auch
in einem frischen Clone.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from src.models.experiment_records import (
    EventRecord,
    EventType,
    SensorStreamRecord,
    TrialRecord,
)

DATA_DIR = PROJECT_ROOT / "data"

requires_project_data = pytest.mark.skipif(
    not (DATA_DIR / "T-1").exists(),
    reason="Lokale Projektdaten (data/) nicht vorhanden — Real-Data-Test übersprungen",
)


def make_fusion_stream(n_samples: int = 31, step_ms: float = 100.0,
                       start_ms: float = 0.0) -> SensorStreamRecord:
    """Synthetischer Fusion-Stream (10 Hz, shimmer + gaze) mit Rampenwerten."""
    ts = [start_ms + i * step_ms for i in range(n_samples)]
    channels = {
        "shimmer.GsrKOhm": [5000.0 - 10.0 * i for i in range(n_samples)],
        "shimmer.PpgmV": [200.0 + 5.0 * (i % 4) for i in range(n_samples)],
        "gaze.LeftX": [0.2 + 0.02 * (i % 10) for i in range(n_samples)],
        "gaze.LeftValidity": [float(i % 2) for i in range(n_samples)],
    }
    return SensorStreamRecord(source="fusion_merged", modality="fusion",
                              timestamps=ts, channels=channels)


def make_trial() -> TrialRecord:
    """Synthetischer Trial: Baseline + 2 Task-Segmente (Domains) + Stream."""
    events = [
        EventRecord(0.0, EventType.BASELINE_START, "baseline:start", {}),
        EventRecord(500.0, EventType.BASELINE_END, "baseline:end", {}),
        EventRecord(600.0, EventType.TASK_START, "task:start", {"domain": "gaming"}),
        EventRecord(1400.0, EventType.TASK_END, "task:end", {"domain": "gaming"}),
        EventRecord(1500.0, EventType.TASK_START, "task:start", {"domain": "health"}),
        EventRecord(2900.0, EventType.TASK_END, "task:end", {"domain": "health"}),
    ]
    return TrialRecord(
        trial_id="T-SYN",
        source_dir="/synthetic",
        events=events,
        streams=[make_fusion_stream()],
    )


@pytest.fixture
def synthetic_trial() -> TrialRecord:
    return make_trial()


@pytest.fixture
def synthetic_stream() -> SensorStreamRecord:
    return make_fusion_stream()
