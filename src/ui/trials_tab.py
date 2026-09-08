"""AP11 – Trials tab: timeline, events, segments, quality."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analysis.statistics import baseline_vs_task, event_density
from src.preprocessing.quality_checks import check_trial
from src.preprocessing.segmentation import build_timeline_from_trial
from src.analysis.reporting import timeline_to_dataframe, quality_reports_to_dataframe
from src.session import get_trials


def render_trials_tab() -> None:
    trials = get_trials()
    if not trials:
        st.info("Keine Trials geladen. → Tab 'Import'")
        return

    trial_ids = [t.trial_id for t in trials]
    selected_id = st.selectbox("Trial auswählen", trial_ids)
    trial = next(t for t in trials if t.trial_id == selected_id)

    inner_tab1, inner_tab2, inner_tab3, inner_tab4 = st.tabs(
        ["Timeline", "Events", "Qualität", "Analysen"]
    )

    # ── Timeline ──────────────────────────────────────────────────────────────
    with inner_tab1:
        st.subheader(f"Timeline: {trial.trial_id}")
        timeline = build_timeline_from_trial(trial)

        if not timeline.segments:
            st.warning("Keine Segmente gefunden (keine Events oder keine erkennbaren Start/End-Paare).")
        else:
            df = timeline_to_dataframe(timeline)
            st.dataframe(df, use_container_width=True)

            incomplete = df[df["complete"] == False]
            if not incomplete.empty:
                st.warning(f"{len(incomplete)} unvollständige(s) Segment(e) ohne End-Event.")

        if timeline.quality_issues:
            st.markdown("**Quality Issues:**")
            for issue in timeline.quality_issues:
                st.error(issue)

        if timeline.segments:
            st.download_button(
                "Timeline CSV",
                data=timeline_to_dataframe(timeline).to_csv(index=False).encode(),
                file_name=f"{trial.trial_id}_timeline.csv",
                mime="text/csv",
                key=f"trials_timeline_csv_{trial.trial_id}",
            )

    # ── Events ────────────────────────────────────────────────────────────────
    with inner_tab2:
        st.subheader(f"Rohe Events: {trial.trial_id}")
        if not trial.events:
            st.info("Keine Events vorhanden.")
        else:
            rows = [
                {"timestamp_ms": e.timestamp, "event_type": e.event_type.value, "label": e.label}
                for e in trial.events
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # ── Qualität ──────────────────────────────────────────────────────────────
    with inner_tab3:
        st.subheader(f"Sensor-Qualität: {trial.trial_id}")
        if not trial.streams:
            st.info("Keine Sensor-Streams vorhanden.")
        else:
            gap_threshold = st.slider("Gap-Schwellenwert (ms)", 100, 10000, 3000, step=100)
            reports = check_trial(trial, gap_threshold_ms=float(gap_threshold))
            df_q = quality_reports_to_dataframe(reports)
            st.dataframe(df_q, use_container_width=True)

            for r in reports:
                if not r.ok:
                    with st.expander(f"Details: {r.source}"):
                        for issue in r.global_issues:
                            st.error(issue)
                        for ch in r.channels:
                            for issue in ch.issues:
                                st.warning(f"{ch.channel}: {issue}")

            st.download_button(
                "Qualitätsreport CSV",
                data=df_q.to_csv(index=False).encode(),
                file_name=f"{trial.trial_id}_quality.csv",
                mime="text/csv",
                key=f"trials_quality_csv_{trial.trial_id}",
            )

    # ── Analysen: Eventdichte + Baseline-vs-Task ──────────────────────────────
    with inner_tab4:
        st.subheader(f"Analysen: {trial.trial_id}")
        timeline = build_timeline_from_trial(trial)

        st.markdown("**Eventdichte** (Events pro Sekunde je Segment)")
        df_density = event_density(timeline, trial)
        if df_density.empty:
            st.info("Keine Events vorhanden.")
        else:
            st.dataframe(df_density, use_container_width=True)
            st.download_button(
                "Eventdichte CSV",
                data=df_density.to_csv(index=False).encode(),
                file_name=f"{trial.trial_id}_event_density.csv",
                mime="text/csv",
                key=f"trials_density_csv_{trial.trial_id}",
            )

        st.markdown("---")
        st.markdown("**Baseline-vs-Task-Vergleich** (Kanal-Mittelwerte je Segmenttyp)")
        if not trial.streams:
            st.info("Keine Sensor-Streams vorhanden.")
        else:
            feature = st.selectbox(
                "Merkmal", ["mean", "median", "std", "max", "min"],
                key="trials_bvt_feature",
            )
            df_bvt = baseline_vs_task(trial, timeline, trial.streams[0], feature=feature)
            if df_bvt.empty:
                st.info("Keine vollständigen Baseline-/Task-Segmente gefunden.")
            else:
                st.dataframe(df_bvt, use_container_width=True)
                st.download_button(
                    "Baseline-vs-Task CSV",
                    data=df_bvt.to_csv(index=False).encode(),
                    file_name=f"{trial.trial_id}_baseline_vs_task.csv",
                    mime="text/csv",
                    key=f"trials_bvt_csv_{trial.trial_id}",
                )
