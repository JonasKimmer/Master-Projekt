"""
Baseline-zentrierte Domänen-Deltas für Pupillendurchmesser und Hautleitwert
(Paper 1, Abschnitt 4.4).

Methode: Je Trial wird die vollständige Baseline mit den meisten gültigen
Sensor-Samples als Referenz gewählt (T-3 hat zwei Baseline-Segmente, von
denen nur das zweite Sensordaten überlappt; T-10s Stream beginnt erst
nach der Baseline und fällt damit raus). Task-Segmente folgen der
FIFO-Paarung der Analyseumgebung (build_timeline). Pro Trial und Domäne
wird der Mittelwert der Task-Samples minus Baseline-Mittelwert gebildet;
berichtete Deltas sind Mittel und Stichproben-SD über Trials.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from src.loaders.trial_loader import load_trials_from_dir
from src.preprocessing.segmentation import build_timeline

DATA_DIR = Path("data")
DOMAINS = ("gaming", "health", "city")
CHANNELS: dict[str, tuple[str, ...]] = {
    "Pupillendurchmesser (mm)": ("gaze.LeftPupilDiamMm", "gaze.RightPupilDiamMm"),
    "Hautleitwert (µS)": ("shimmer.GsrConductanceUS",),
}


def _channel_values(stream, channels: tuple[str, ...], mask: np.ndarray) -> list[float]:
    vals = []
    for c in channels:
        if c in stream.channels:
            vals.extend(v for v in np.array(stream.channels[c])[mask] if v is not None)
    return vals


def sensor_deltas(data_dir: Path | str = DATA_DIR) -> dict[str, dict[str, np.ndarray]]:
    """{Kanal: {Domäne: Array der Trial-Deltas}}."""
    result: dict[str, dict[str, list[float]]] = {k: {} for k in CHANNELS}
    for trial in load_trials_from_dir(str(data_dir)):
        timeline = build_timeline(trial.trial_id, trial.events)
        if not trial.streams:
            continue
        stream = trial.streams[0]
        ts = np.array(stream.timestamps)

        # Baseline mit den meisten gültigen Sensor-Samples
        best, best_n = None, 0
        for seg in timeline.segments:
            if seg.segment_type == "baseline" and seg.is_complete:
                m = (ts >= seg.start_ms) & (ts <= seg.end_ms)
                n = sum(1 for chans in CHANNELS.values() for c in chans
                        if c in stream.channels
                        for v in np.array(stream.channels[c])[m] if v is not None)
                if n > best_n:
                    best, best_n = seg, n
        if best is None:
            continue

        bmask = (ts >= best.start_ms) & (ts <= best.end_ms)
        for label, chans in CHANNELS.items():
            bvals = _channel_values(stream, chans, bmask)
            if not bvals:
                continue
            bmean = float(np.mean(bvals))
            per_domain: dict[str, list[float]] = {}
            for seg in timeline.segments:
                if seg.segment_type == "task" and seg.is_complete and seg.domain:
                    m = (ts >= seg.start_ms) & (ts <= seg.end_ms)
                    vals = _channel_values(stream, chans, m)
                    if vals:
                        per_domain.setdefault(seg.domain, []).append(float(np.mean(vals)) - bmean)
            for d, vlist in per_domain.items():
                result[label].setdefault(d, []).append(float(np.mean(vlist)))
    return {k: {d: np.array(v) for d, v in doms.items()} for k, doms in result.items()}


def main() -> None:
    deltas = sensor_deltas(DATA_DIR)
    print(f"{'Kanal':26} {'Gaming Δ (SD)':>18} {'Gesundheit Δ (SD)':>20} {'Stadt Δ (SD)':>16}")
    for label, doms in deltas.items():
        cells = []
        for d in DOMAINS:
            v = doms.get(d, np.array([]))
            cells.append(f"{v.mean():+.2f} ({v.std(ddof=1):.2f})" if len(v) else "–")
        ns = {d: len(doms.get(d, [])) for d in DOMAINS}
        print(f"{label:26} {cells[0]:>18} {cells[1]:>20} {cells[2]:>16}  n={ns}")


if __name__ == "__main__":
    main()
