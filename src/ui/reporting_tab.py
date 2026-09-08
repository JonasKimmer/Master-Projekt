"""AP11/AP12 – Reporting tab: markdown and CSV exports for all data types."""

from __future__ import annotations

import streamlit as st

from src.analysis.reporting import (
    df_to_csv_bytes,
    df_to_excel_bytes,
    quality_reports_to_dataframe,
    str_to_bytes,
    timeline_to_dataframe,
    trial_markdown_report,
    website_markdown_report,
    websites_to_dataframe,
)
from src.feature_engineering.web_features import pages_to_dataframe
from src.preprocessing.quality_checks import check_trial
from src.preprocessing.segmentation import build_timeline_from_trial
from src.session import get_trials, get_websites


def render_reporting_tab() -> None:
    st.subheader("Export & Reporting")

    # ── Trial reports ─────────────────────────────────────────────────────────
    trials = get_trials()
    if trials:
        st.markdown("#### Trial-Exporte")
        selected = st.selectbox("Trial", [t.trial_id for t in trials], key="rep_trial")
        trial = next(t for t in trials if t.trial_id == selected)
        timeline = build_timeline_from_trial(trial)
        quality_reports = check_trial(trial)

        c1, c2, c3 = st.columns(3)
        with c1:
            df_tl = timeline_to_dataframe(timeline)
            st.download_button(
                "Timeline CSV",
                data=df_to_csv_bytes(df_tl),
                file_name=f"{selected}_timeline.csv",
                mime="text/csv",
                key=f"rep_timeline_csv_{selected}",
            )
        with c2:
            df_q = quality_reports_to_dataframe(quality_reports)
            st.download_button(
                "Qualitätsreport CSV",
                data=df_to_csv_bytes(df_q),
                file_name=f"{selected}_quality.csv",
                mime="text/csv",
                key=f"rep_quality_csv_{selected}",
            )
        with c3:
            st.download_button(
                "Trial Markdown Report",
                data=str_to_bytes(trial_markdown_report(timeline)),
                file_name=f"{selected}_report.md",
                mime="text/markdown",
                key=f"rep_trial_md_{selected}",
            )

    st.markdown("---")

    # ── Website reports ───────────────────────────────────────────────────────
    websites = get_websites()
    if websites:
        st.markdown("#### Website-Exporte")
        sel_w = st.selectbox("Website", [w.website_id for w in websites], key="rep_web")
        website = next(w for w in websites if w.website_id == sel_w)

        c1, c2, c3 = st.columns(3)
        with c1:
            df_pages = pages_to_dataframe(website)
            st.download_button(
                "Pages CSV",
                data=df_to_csv_bytes(df_pages),
                file_name=f"website_{sel_w}_pages.csv",
                mime="text/csv",
                key=f"rep_pages_csv_{sel_w}",
            )
        with c2:
            st.download_button(
                "Pages Excel",
                data=df_to_excel_bytes(df_pages, sheet_name="Pages"),
                file_name=f"website_{sel_w}_pages.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"rep_pages_xlsx_{sel_w}",
            )
        with c3:
            st.download_button(
                "Website Markdown Report",
                data=str_to_bytes(website_markdown_report(website)),
                file_name=f"website_{sel_w}_report.md",
                mime="text/markdown",
                key=f"rep_web_md_{sel_w}",
            )

        st.markdown("---")
        st.markdown("**Alle Websites zusammen:**")
        df_all = websites_to_dataframe(websites)
        st.dataframe(df_all, use_container_width=True)
        st.download_button(
            "Alle Websites CSV",
            data=df_to_csv_bytes(df_all),
            file_name="websites_overview.csv",
            mime="text/csv",
            key="rep_all_websites_csv",
        )

    if not trials and not websites:
        st.info("Noch keine Trial- oder Website-Daten geladen. → Tab 'Import'")
