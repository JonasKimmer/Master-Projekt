"""Trial- und Sensoranalysen: Eventdichte, Baseline-vs-Task, auffällige Fenster.

Diese Funktionen arbeiten ausschließlich auf bereits geladenen Strukturen
(TrialRecord, TrialTimeline, SensorStreamRecord) bzw. auf aggregierten
Fenster-Merkmalen — nicht auf Rohzeitreihen.
"""

from __future__ import annotations

import pandas as pd

from src.feature_engineering.sensor_features import compute_window_features
from src.models.experiment_records import (
    EventType,
    SensorStreamRecord,
    TrialRecord,
    TrialTimeline,
)
from src.preprocessing.windowing import slice_stream

# ── Eventdichte ───────────────────────────────────────────────────────────────

def event_density(timeline: TrialTimeline, trial: TrialRecord) -> pd.DataFrame:
    """
    Events pro Sekunde je Segment und für den gesamten Trial.

    Ein Event wird dem *frühesten* Segment zugewiesen, das seinen Timestamp
    enthält ([start, end]; unvollständige Segmente bis zur letzten Event-Zeit).
    Grenzereignisse, die gleichzeitig das Ende eines und den Start des
    nächsten Segments markieren (z. B. task:end + task:start am selben
    Timestamp), werden dadurch genau einmal gezählt.
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

    # Segmente sind nach Start sortiert. Ein Event wird höchstens einmal
    # zugewiesen; liegt ein Event genau auf einer Segmentgrenze (Ende des
    # einen = Start des nächsten), bestimmt der Event-Typ das Ziel:
    # END-Events zählen zum früheren, START-Events zum späteren Segment.
    counts: dict[int, int] = {id(seg): 0 for seg in timeline.segments}
    for e in trial.events:
        containing = [
            seg for seg in timeline.segments
            if seg.start_ms <= e.timestamp <= (seg.end_ms if seg.end_ms is not None else last_event_ts)
        ]
        if not containing:
            continue
        if len(containing) > 1 and e.event_type in (EventType.TASK_START, EventType.BASELINE_START, EventType.QUESTIONNAIRE_START):
            counts[id(containing[-1])] += 1
        else:
            counts[id(containing[0])] += 1

    for seg in timeline.segments:
        end = seg.end_ms if seg.end_ms is not None else last_event_ts
        dur_s = max((end - seg.start_ms) / 1000.0, 1e-9)
        n = counts[id(seg)]
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
    timeline: TrialTimeline,
    stream: SensorStreamRecord,
    feature: str = "mean",
) -> pd.DataFrame:
    """
    Vergleicht Kanal-Merkmale zwischen Baseline- und Task-Segmenten.

    Gruppiert wird nach ``segment_type`` (nicht nach dem Label — ein
    Baseline-Segment darf auch 'rest' heißen). Wiederholte Segmente
    gleichen Typs fließen alle ein (kein Überschreiben); fehlende
    Einzelwerte (Kanal in einem Segment nicht messbar) werden bei der
    Mittelwertbildung übersprungen statt als NaN zu propagieren.
    """
    segs = [
        s for s in timeline.segments
        if s.end_ms is not None and s.segment_type in ("baseline", "task")
    ]
    if not segs:
        return pd.DataFrame()

    # groups[segment_type] = Liste von {channel: wert} je Segment
    groups: dict[str, list[dict[str, float]]] = {"baseline": [], "task": []}
    for seg in segs:
        sliced = slice_stream(stream, seg.start_ms, seg.end_ms)
        feats = compute_window_features(sliced)
        if feats:
            groups[seg.segment_type].append(
                {ch: f[feature] for ch, f in feats.items() if f.get(feature) is not None}
            )

    all_channels = sorted(
        {ch for dicts in groups.values() for d in dicts for ch in d}
    )
    rows = []
    for ch in all_channels:
        row: dict = {"channel": ch}
        means: dict[str, float] = {}
        for g in ("baseline", "task"):
            vals = [d[ch] for d in groups[g] if ch in d]
            means[g] = sum(vals) / len(vals) if vals else float("nan")
            row[f"n_{g}_segments"] = len(vals)
        row["baseline_mean"] = round(means["baseline"], 6)
        row["task_mean"] = round(means["task"], 6)
        if any(v != v for v in means.values()):  # NaN-check
            row["delta_task_minus_baseline"] = float("nan")
        else:
            row["delta_task_minus_baseline"] = round(means["task"] - means["baseline"], 6)
        rows.append(row)
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
