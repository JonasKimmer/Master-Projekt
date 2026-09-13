"""AP11 – Website tab: page inventory, features, screenshot preview."""

from __future__ import annotations


import pandas as pd
import streamlit as st

from src.analysis.web_consistency import consistency_summary, website_consistency
from src.feature_engineering.web_features import pages_to_dataframe, website_features
from src.session import get_websites


def render_website_tab() -> None:
    websites = get_websites()
    if not websites:
        st.info("Keine Websites geladen. → Tab 'Import'")
        return

    website_ids = [w.website_id for w in websites]
    selected_id = st.selectbox("Website auswählen", website_ids, key="web_select")
    website = next(w for w in websites if w.website_id == selected_id)

    # Korrupte statt fehlende Artefakte sichtbar machen — Nullwerte aus
    # unlesbaren Dateien dürfen nicht als 'nicht gecrawlt' durchgehen
    broken = {p.page_id: p.load_errors for p in website.pages if p.load_errors}
    if broken:
        with st.expander(f"⚠️ {len(broken)} Seite(n) mit unlesbaren Artefakten", expanded=False):
            for page_id, errs in broken.items():
                st.markdown(f"**Seite {page_id}**: " + ", ".join(
                    f"`{name}` ({reason})" for name, reason in errs.items()))
            st.caption("Diese Merkmale werden als 0 gezählt, obwohl die Datei "
                       "existiert — Ursache prüfen statt als 'nicht gecrawlt' lesen.")

    inner_tab1, inner_tab2, inner_tab3, inner_tab4 = st.tabs(
        ["Seiten-Übersicht", "Features", "Screenshots", "Konsistenz"]
    )

    # ── Page overview ─────────────────────────────────────────────────────────
    with inner_tab1:
        st.subheader(f"Seiten: Website {website.website_id}")
        st.caption(f"Pfad: {website.source_dir}")
        if website.portal_meta:
            with st.expander("Portal-Metadaten"):
                st.json(website.portal_meta)

        if website.asset_index:
            n_assets = website.asset_index.get("n_assets", 0)
            n_shared = website.asset_index.get("n_shared", 0)
            with st.expander(f"Asset-Index ({n_assets} Assets, {n_shared} shared)"):
                assets = website.asset_index.get("assets", {})
                shared_rows = [
                    {"url": url, "typ": a.get("type"), "seiten": a.get("pages"),
                     "lokal": a.get("local_path", "")}
                    for url, a in assets.items() if a.get("shared")
                ]
                if shared_rows:
                    st.dataframe(pd.DataFrame(shared_rows), use_container_width=True)
                else:
                    st.info("Keine von mehreren Seiten geteilten Assets vorhanden.")
                if website.shared_assets_dir:
                    st.caption(f"Shared-Assets-Ordner: {website.shared_assets_dir}")

        df = pages_to_dataframe(website)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Keine Seiten gefunden.")

    # ── Features ──────────────────────────────────────────────────────────────
    with inner_tab2:
        st.subheader(f"Aggregierte Features: Website {website.website_id}")
        feats = website_features(website)
        col1, col2, col3 = st.columns(3)
        col1.metric("Seiten",       feats.get("page_count", 0))
        col2.metric("Links gesamt", feats.get("link_count_sum", 0))
        col3.metric("Media gesamt", feats.get("media_count_sum", 0))

        st.markdown("---")
        st.markdown("**Alle Features:**")
        pages_df = pages_to_dataframe(website)
        if pages_df.empty:
            st.info("Keine Seiten vorhanden.")
        else:
            st.dataframe(pages_df.describe().T, use_container_width=True)
            st.download_button(
                "Features CSV",
                data=pages_df.to_csv(index=False).encode(),
                file_name=f"website_{website.website_id}_features.csv",
                mime="text/csv",
                key=f"web_features_csv_{website.website_id}",
            )

    # ── Screenshots ───────────────────────────────────────────────────────────
    with inner_tab3:
        st.subheader(f"Screenshots: Website {website.website_id}")
        pages_with_screenshots = [p for p in website.pages if p.has_screenshot]
        if not pages_with_screenshots:
            st.info("Keine Screenshots vorhanden.")
        else:
            cols = st.columns(min(3, len(pages_with_screenshots)))
            for i, page in enumerate(pages_with_screenshots):
                with cols[i % 3]:
                    st.caption(f"Seite {page.page_id} — {page.url or 'URL unbekannt'}")
                    st.image(page.screenshot_path, use_container_width=True)

    # ── Konsistenzanalyse Screenshots ↔ JSON-Merkmale (AP10) ─────────────────
    with inner_tab4:
        st.subheader(f"Konsistenzanalyse: Website {website.website_id}")
        df_cons = website_consistency(website)
        if df_cons.empty:
            st.info("Keine Seiten vorhanden.")
        else:
            summary = consistency_summary(df_cons)
            c1, c2, c3 = st.columns(3)
            c1.metric("Seiten", summary["pages"])
            c2.metric("Mit Screenshot", summary["mit_screenshot"])
            c3.metric("Auffällige Seiten", summary["auffällige_seiten"])
            if summary["auffällige_seiten"]:
                st.warning(f"{summary['auffällige_seiten']} Seite(n) mit "
                           f"{summary['befunde']} Befund(en):")
                st.dataframe(df_cons[df_cons["n_issues"] > 0], use_container_width=True)
            else:
                st.success("Keine Konsistenzbefunde — Screenshots und JSON-"
                           "Merkmale passen zusammen.")
            st.download_button(
                "Konsistenztabelle CSV",
                data=df_cons.to_csv(index=False).encode(),
                file_name=f"website_{website.website_id}_consistency.csv",
                mime="text/csv",
                key=f"web_consistency_csv_{website.website_id}",
            )
