"""AP13 – ML tab: clustering, anomaly detection, classification, regression."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analysis.ml_analysis import (
    prepare_features,
    run_classification,
    run_isolation_forest,
    run_kmeans,
    run_regression,
)
from src.session import get_tabular, has_tabular


def render_ml_tab() -> None:
    st.subheader("ML-Analyse")
    st.caption("Arbeitet auf aggregierten Feature-Tabellen (tabellarische Daten oder exportierte Window-Features).")

    if not has_tabular():
        st.info("Bitte zuerst eine Feature-Tabelle als CSV hochladen (Sidebar).")
        return

    df, _ = get_tabular()
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols = df.columns.tolist()

    if not numeric_cols:
        st.warning("Keine numerischen Spalten gefunden.")
        return

    mode = st.radio(
        "Analysemodus",
        ["Clustering (K-Means)", "Anomalie-Erkennung", "Klassifikation", "Regression"],
        horizontal=True,
    )

    drop_cols = st.multiselect("Spalten ausschließen (IDs, Labels, …)", all_cols, key="ml_drop")
    target_options = [c for c in all_cols if c not in drop_cols]
    X, feature_names = prepare_features(df, drop_cols)

    if X.empty or X.shape[1] < 1:
        st.warning("Keine verwendbaren Features nach Filter.")
        return

    st.caption(f"{X.shape[0]} Zeilen · {X.shape[1]} Features")

    # ── Clustering ────────────────────────────────────────────────────────────
    if mode == "Clustering (K-Means)":
        k = st.slider("Anzahl Cluster (k)", 2, 10, 3)
        if st.button("K-Means ausführen", key="ml_kmeans"):
            try:
                result = run_kmeans(X, k)
            except ValueError as e:
                st.error(f"K-Means fehlgeschlagen: {e}")
            else:
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.metric("Silhouette Score", result["silhouette"])
                    st.metric("Inertia", result["inertia"])
                    labeled = df.copy()
                    labeled["cluster"] = result["labels"]
                    st.dataframe(labeled, use_container_width=True)
                    st.download_button(
                        "Cluster-Ergebnis CSV",
                        data=labeled.to_csv(index=False).encode(),
                        file_name="kmeans_result.csv",
                        mime="text/csv",
                        key="ml_kmeans_dl",
                    )

    # ── Anomaly Detection ─────────────────────────────────────────────────────
    elif mode == "Anomalie-Erkennung":
        contamination = st.slider("Erwarteter Anomalie-Anteil (%)", 1, 20, 5) / 100
        if st.button("Isolation Forest ausführen", key="ml_iforest"):
            try:
                result = run_isolation_forest(X, contamination)
            except ValueError as e:
                st.error(f"Isolation Forest fehlgeschlagen: {e}")
            else:
                st.metric("Anomalien gefunden", result["n_anomalies"])
                st.metric("Anomalie-Rate", f"{result['anomaly_rate']*100:.1f}%")
                labeled = df.copy()
                labeled["anomaly"] = ["⚠️ Anomalie" if l == -1 else "✓ Normal" for l in result["labels"]]
                st.dataframe(labeled, use_container_width=True)
                st.download_button(
                    "Anomalie-Ergebnis CSV",
                    data=labeled.to_csv(index=False).encode(),
                    file_name="anomaly_result.csv",
                    mime="text/csv",
                    key="ml_iforest_dl",
                )

    # ── Classification ────────────────────────────────────────────────────────
    elif mode == "Klassifikation":
        if not target_options:
            st.warning("Keine Zielvariable verfügbar (alle Spalten sind ausgeschlossen).")
            return
        target = st.selectbox("Zielvariable (Kategorie)", target_options, key="ml_clf_target")
        if st.button("Random Forest (Klassifikation)", key="ml_clf"):
            try:
                result = run_classification(df.drop(columns=drop_cols, errors="ignore"), target)
            except ValueError as e:
                st.error(f"Klassifikation fehlgeschlagen: {e}")
            else:
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.markdown("**Top Features:**")
                    st.dataframe(pd.Series(result["top_features"]).rename("Importance"), use_container_width=True)
                    st.markdown("**Classification Report:**")
                    st.dataframe(pd.DataFrame(result["report"]).T, use_container_width=True)

    # ── Regression ────────────────────────────────────────────────────────────
    elif mode == "Regression":
        numeric_target_options = [c for c in numeric_cols if c in target_options]
        if not numeric_target_options:
            st.warning("Keine numerische Zielvariable verfügbar.")
            return
        target = st.selectbox("Zielvariable (numerisch)", numeric_target_options, key="ml_reg_target")
        if st.button("Random Forest (Regression)", key="ml_reg"):
            try:
                result = run_regression(df.drop(columns=drop_cols, errors="ignore"), target)
            except ValueError as e:
                st.error(f"Regression fehlgeschlagen: {e}")
            else:
                if "error" in result:
                    st.error(result["error"])
                else:
                    col1, col2 = st.columns(2)
                    col1.metric("MAE", result["mae"])
                    col2.metric("R²", result["r2"])
                    st.markdown("**Top Features:**")
                    st.dataframe(pd.Series(result["top_features"]).rename("Importance"), use_container_width=True)
