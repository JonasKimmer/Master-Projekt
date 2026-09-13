"""AP11 – Sensoranalyse-Tab: modality-bezogene Übersicht über alle Trials.

Bündelt die Sensor-Perspektive, die bisher auf Trials (Qualität) und
Zeitfenster verteilt war, in einem eigenen Tab:

  * Qualitäts-Übersicht je Trial und Modalität (Split + Checks)
  * Kanalstatistik (Samples, Fehlerrate, Min/Max/Mittelwert) je Modalität
  * CSV-Export beider Übersichten
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.preprocessing.quality_checks import check_stream
from src.preprocessing.synchronization import split_fusion_stream
from src.session import get_trials


def _sensor_parts(trial):
    """Trial in Modalitäts-Streams zerlegen (fusion → shimmer/gaze/…)."""
    parts = []
    for s in trial.streams:
        parts.extend(split_fusion_stream(s))
    return parts


def render_sensor_tab() -> None:
    trials = get_trials()
    if not trials:
        st.info("Keine Trials geladen. → Tab 'Import'")
        return

    st.subheader("Sensoranalyse")
    st.caption("Modalitätsbezogene Qualitäts- und Kanalübersicht über alle geladenen Trials.")

    # Verfügbare Modalitäten über alle Trials ermitteln
    modality_map: dict[str, list] = {}
    for t in trials:
        for part in _sensor_parts(t):
            if part.timestamps:
                modality_map.setdefault(part.modality, []).append((t, part))
    if not modality_map:
        st.warning("Keine Sensor-Streams mit Daten vorhanden.")
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        modality = st.selectbox("Modalität", sorted(modality_map), key="sensor_modality")
        gap_threshold = st.slider("Gap-Schwellenwert (ms)", 100, 10000, 3000, step=100,
                                  key="sensor_gap")
        pairs = modality_map[modality]

    with col2:
        st.markdown(f"#### Qualität je Trial — Modalität `{modality}`")
        q_rows = []
        for trial, part in pairs:
            rep = check_stream(trial.trial_id, part, gap_threshold_ms=float(gap_threshold))
            q_rows.append({
                "trial": trial.trial_id,
                "samples": rep.n_timestamps,
                "dup_timestamps": rep.duplicate_timestamps,
                "max_gap_ms": round(rep.max_gap_ms),
                "n_kanäle": len(part.channels),
                "issues": len(rep.global_issues) + sum(len(c.issues) for c in rep.channels),
                "ok": rep.ok,
            })
        df_q = pd.DataFrame(q_rows)
        st.dataframe(df_q, use_container_width=True)
        st.download_button(
            "Qualitäts-Übersicht CSV",
            data=df_q.to_csv(index=False).encode(),
            file_name=f"sensor_quality_{modality}.csv",
            mime="text/csv",
            key=f"sensor_quality_csv_{modality}",
        )

    st.markdown("---")
    st.markdown(f"#### Kanalstatistik — Modalität `{modality}`")
    # Kanalstatistik je gewähltem Trial (Kanalmengen unterscheiden sich
    # zwischen Trials/Modalitäten, eine gemeinsame Tabelle wäre lückenhaft)
    ch_rows = []
    trial_ids = [t.trial_id for t, _ in pairs]
    sel_trial = st.selectbox("Trial für Kanalstatistik", trial_ids, key="sensor_trial")
    part = next(p for t, p in pairs if t.trial_id == sel_trial)
    for ch, values in part.channels.items():
        valid = [v for v in values if v is not None]
        ch_rows.append({
            "kanal": ch,
            "samples": len(values),
            "gültige": len(valid),
            "missing_rate": round(1.0 - len(valid) / len(values), 4) if values else 1.0,
            "min": round(min(valid), 4) if valid else None,
            "max": round(max(valid), 4) if valid else None,
            "mittelwert": round(sum(valid) / len(valid), 4) if valid else None,
        })
    if ch_rows:
        df_ch = pd.DataFrame(ch_rows)
        st.dataframe(df_ch, use_container_width=True)
        st.download_button(
            "Kanalstatistik CSV",
            data=df_ch.to_csv(index=False).encode(),
            file_name=f"sensor_channels_{sel_trial}_{modality}.csv",
            mime="text/csv",
            key=f"sensor_channels_csv_{sel_trial}",
        )
    else:
        st.info("Keine Kanäle in dieser Modalität.")
