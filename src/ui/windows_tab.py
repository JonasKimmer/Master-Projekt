"""AP11 – Windows tab: configure time windows and compute sensor features."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.models.experiment_records import WindowDefinition
from src.preprocessing.segmentation import build_timeline_from_trial
from src.preprocessing.windowing import generate_windows, slice_stream
from src.feature_engineering.sensor_features import compute_window_features
from src.session import get_trials


def render_windows_tab() -> None:
    trials = get_trials()
    if not trials:
        st.info("Keine Trials geladen. → Tab 'Import'")
        return

    st.subheader("Zeitfenster-Manager")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### Konfiguration")
        trial_id = st.selectbox("Trial", [t.trial_id for t in trials], key="win_trial")
        trial = next(t for t in trials if t.trial_id == trial_id)

        stream_options = [s.source for s in trial.streams]
        if not stream_options:
            st.warning("Kein Stream vorhanden.")
            return
        stream_src = st.selectbox("Stream", stream_options, key="win_stream")
        stream = next(s for s in trial.streams if s.source == stream_src)

        mode = st.radio("Modus", ["sliding", "fixed", "task"], key="win_mode")
        duration = st.number_input("Fensterlänge (ms)", min_value=100, value=2000, step=100)

        step = None
        task_label = None
        task_timeline = None
        if mode == "sliding":
            step = st.number_input("Schrittweite (ms)", min_value=100, value=1000, step=100)
        elif mode == "task":
            task_timeline = build_timeline_from_trial(trial)
            labels = list({s.label for s in task_timeline.segments})
            if labels:
                task_label = st.selectbox("Task-Label", labels)
            else:
                st.warning("Trial hat keine Segmente (keine Events oder keine erkennbaren Start/End-Paare) — Task-Modus benötigt Event-Daten.")

        offset_start = st.number_input("Offset Start (ms)", value=0, step=100)
        offset_end   = st.number_input("Offset Ende (ms)", value=0, step=100)

    with col2:
        st.markdown("#### Ergebnisse")
        if st.button("Fenster berechnen", key="win_compute"):
            definition = WindowDefinition(
                window_id="manual",
                mode=mode,
                duration_ms=float(duration),
                step_ms=float(step) if step else None,
                task_label=task_label,
                offset_start_ms=float(offset_start),
                offset_end_ms=float(offset_end),
            )
            windows = generate_windows(stream, definition, task_timeline)

            if not windows:
                st.warning("Keine Fenster generiert.")
            else:
                st.info(f"{len(windows)} Fenster generiert.")
                all_rows = []
                for i, (start, end) in enumerate(windows):
                    sliced = slice_stream(stream, start, end)
                    feats = compute_window_features(sliced)
                    for ch, ch_feats in feats.items():
                        row = {"window": i, "start_ms": round(start), "end_ms": round(end), "channel": ch}
                        row.update(ch_feats)
                        all_rows.append(row)

                if all_rows:
                    df = pd.DataFrame(all_rows)
                    st.dataframe(df, use_container_width=True)
                    st.download_button(
                        "Features CSV",
                        data=df.to_csv(index=False).encode(),
                        file_name=f"{trial_id}_windows.csv",
                        mime="text/csv",
                        key=f"win_features_csv_{trial_id}",
                    )
                else:
                    st.warning("Keine numerischen Merkmale berechenbar.")
