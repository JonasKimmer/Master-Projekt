"""AP11 – Inventory tab: overview of all loaded data sources."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.session import get_trials, get_websites, has_tabular, get_tabular


def render_inventory_tab() -> None:
    st.subheader("Geladene Datensätze")

    # ── Tabular ───────────────────────────────────────────────────────────────
    st.markdown("#### Tabellarische Daten")
    if has_tabular():
        df, _ = get_tabular()
        st.success(f"1 Datei geladen — {df.shape[0]} Zeilen, {df.shape[1]} Spalten")
    else:
        st.info("Keine tabellarischen Daten geladen.")

    # ── Trials ────────────────────────────────────────────────────────────────
    st.markdown("#### Experiment-Trials")
    trials = get_trials()
    if trials:
        rows = []
        for t in trials:
            rows.append({
                "Trial ID":    t.trial_id,
                "Events":      len(t.events),
                "Streams":     len(t.streams),
                "Channels":    sum(len(s.channels) for s in t.streams),
                "Samples":     sum(len(s.timestamps) for s in t.streams),
                "Pfad":        t.source_dir,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("Keine Trials geladen. → Tab 'Import'")

    # ── Websites ──────────────────────────────────────────────────────────────
    st.markdown("#### Webcrawler-Daten")
    websites = get_websites()
    if websites:
        rows = []
        for w in websites:
            rows.append({
                "Website ID":   w.website_id,
                "Pages":        w.page_count,
                "Total Links":  w.total_links,
                "Total Media":  w.total_media,
                "Pfad":         w.source_dir,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("Keine Websites geladen. → Tab 'Import'")
