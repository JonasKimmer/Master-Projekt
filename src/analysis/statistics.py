"""Trial- und Sensoranalysen: Eventdichte, Baseline-vs-Task, auffällige Fenster.

Diese Funktionen arbeiten ausschließlich auf bereits geladenen Strukturen
(TrialRecord, TrialTimeline, SensorStreamRecord) bzw. auf aggregierten
Fenster-Merkmalen — nicht auf Rohzeitreihen.
"""

from __future__ import annotations

import pandas as pd

from src.feature_engineering.sensor_features import compute_window_features
from src.models.experiment_records import SensorStreamRecord, TrialRecord, TrialTimeline
from src.preprocessing.windowing import slice_stream

# ── Eventdichte ───────────────────────────────────────────────────────────────

def event_density(timeline: TrialTimeline, trial: TrialRecord) -> pd.DataFrame:
    """
    Events pro Sekunde je Segment und für den gesamten Trial.

    Ein Event zählt zu einem Segment, wenn sein Timestamp in
    [start_ms, end_ms] liegt (unvollständige Segmente ohne Ende werden bis
    zur letzten Event-Zeit ausgwertet — bewusst tolerant, da die Rohdaten
    laut Plan nicht immer End-Events haben).
    """
    if not trial.events:
        return pd.DataFrame()

    last_event_ts = max(e.timestamp for e in trial.events)
    rows: list[dict] = []

    total_start = min(e.timestamp for e in trial.events)
    total_dur_s = max((last_event_ts - total_start) / 1000.0, 1e-9)
    rows.append({
        "trial_id": trial.trial_id,
        "segment": "<gesamt>",
        "type": "",
        "start_ms": total_start,
        "end_ms": last_event_ts,
        "duration_s": round(total_dur_s, 3),
        "n_events": len(trial.events),
        "events_per_s": round(len(trial.events) / total_dur_s, 4),
    })

    for seg in timeline.segments:
        end = seg.end_ms if seg.end_ms is not None else last_event_ts
        dur_s = max((end - seg.start_ms) / 1000.0, 1e-9)
        n = sum(1 for e in trial.events if seg.start_ms <= e.timestamp <= end)
        domain = getattr(seg, "domain", None) or ""
        rows.append({
            "trial_id": trial.trial_id,
            "segment": seg.label + (f" [{domain}]" if domain else ""),
            "type": seg.segment_type,
            "start_ms": seg.start_ms,
            "end_ms": end,
            "duration_s": round(dur_s, 3),
            "n_events": n,
            "events_per_s": round(n / dur_s, 4),
        })

    return pd.DataFrame(rows)


# ── Baseline-vs-Task-Vergleich ────────────────────────────────────────────────

def baseline_vs_task(
    trial: TrialRecord,
    timeline: TrialTimeline,
    stream: SensorStreamRecord,
    feature: str = "mean",
) -> pd.DataFrame:
    """
    Vergleicht Kanal-Merkmale zwischen Baseline- und Task-Segmenten.

    Pro Segment wird der Kanal-Mittelwert (bzw. ``feature``) über die
    Samples im Segment berechnet; ausgegeben wird pro Kanal der
    Baseline-Mittelwert, der Task-Mittelwert und deren Differenz
    (Task − Baseline). Segmente mit Domain-Info (falls vorhanden) werden
    zusätzlich einzeln ausgewiesen.
    """
    segs = [s for s in timeline.segments if s.end_ms is not None]
    segs = [s for s in segs if s.segment_type in ("baseline", "task")]
    if not segs:
        return pd.DataFrame()

    per_segment: dict[str, dict[str, float]] = {}
    for seg in segs:
        sliced = slice_stream(stream, seg.start_ms, seg.end_ms)
        feats = compute_window_features(sliced)
        if not feats:
            continue
        domain = getattr(seg, "domain", None)
        key = seg.label + (f" [{domain}]" if domain else "")
        per_segment[key] = {ch: f.get(feature, float("nan")) for ch, f in feats.items()}

    if not per_segment:
        return pd.DataFrame()

    base_keys = [k for k in per_segment if k.startswith("baseline")]
    task_keys = [k for k in per_segment if k.startswith("task")]
    all_channels = sorted({ch for d in per_segment.values() for ch in d})

    rows = []
    for ch in all_channels:
        base_vals = [per_segment[k][ch] for k in base_keys if ch in per_segment[k]]
        task_vals = [per_segment[k][ch] for k in task_keys if ch in per_segment[k]]
        base_mean = sum(base_vals) / len(base_vals) if base_vals else float("nan")
        task_mean = sum(task_vals) / len(task_vals) if task_vals else float("nan")
        rows.append({
            "channel": ch,
            "baseline_mean": round(base_mean, 6),
            "task_mean": round(task_mean, 6),
            "delta_task_minus_baseline": round(task_mean - base_mean, 6),
        })
    return pd.DataFrame(rows)


# ── Auffällige Fenster ────────────────────────────────────────────────────────

def notable_windows(
    features_df: pd.DataFrame,
    z_threshold: float = 2.0,
    min_samples: int = 5,
) -> pd.DataFrame:
    """
    Markiert auffällige Fenster in einer langen Feature-Tabelle
    (Spalten: window, start_ms, end_ms, channel, mean, std, n_samples, …).

    Kriterien (pro Kanal, z-Score über alle Fenster desselben Kanals):
      * |z(mean)|  > z_threshold            → starke Aktivierungsverschiebung
      * |z(std)|   > z_threshold            → starke Variabilität
      * n_samples  < min_samples             → schlechte Datenqualität
    Die Rückgabe enthält nur die flagged Zeilen inkl. Spalte ``reason``.
    """
    if features_df.empty or "channel" not in features_df.columns:
        return pd.DataFrame()

    df = features_df.copy()
    for col in ("mean", "std"):
        if col in df.columns:
            grp = df.groupby("channel")[col]
            mean, std = grp.transform("mean"), grp.transform("std")
            df[f"z_{col}"] = (df[col] - mean) / std.replace(0, pd.NA)

    reasons: list[str] = []
    for _, row in df.iterrows():
        why = []
        if "z_mean" in df.columns and pd.notna(row.get("z_mean")) and abs(row["z_mean"]) > z_threshold:
            why.append(f"mean z={row['z_mean']:+.1f}")
        if "z_std" in df.columns and pd.notna(row.get("z_std")) and abs(row["z_std"]) > z_threshold:
            why.append(f"std z={row['z_std']:+.1f}")
        if "n_samples" in df.columns and pd.notna(row.get("n_samples")) and row["n_samples"] < min_samples:
            why.append(f"nur {row['n_samples']} Samples")
        reasons.append("; ".join(why))

    df["reason"] = reasons
    flagged = df[df["reason"] != ""].copy()
    cols = [c for c in ("window", "start_ms", "end_ms", "channel",
                        "mean", "std", "z_mean", "z_std", "n_samples", "reason") if c in flagged.columns]
    return flagged[cols]
