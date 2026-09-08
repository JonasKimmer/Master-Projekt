import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from src.analysis.reporting import df_to_csv_bytes, df_to_excel_bytes


def _safe_value_counts(series: pd.Series, dropna: bool = True) -> pd.Series:
    """value_counts() that falls back to string coercion for unhashable dtypes."""
    try:
        return series.value_counts(dropna=dropna)
    except TypeError:
        return series.astype(str).value_counts(dropna=dropna)


def _text_search_mask(df: pd.DataFrame, term: str) -> pd.Series:
    """Mask der Zeilen, deren Zellen den Suchterm literal enthalten.

    regex=False: Eingaben wie '(' oder '[abc]' sind Suchbegriffe, keine
    Regex-Muster — mit dem Default (regex=True) crasht str.contains mit
    re.error und reißt die ganze Ansicht mit.
    """
    return (
        df.astype(str)
        .apply(lambda x: x.str.contains(term, case=False, regex=False))
        .any(axis=1)
    )


def _slider_bounds(series: pd.Series) -> tuple[float, float] | None:
    """(min, max) einer numerischen Spalte, oder None, wenn kein sinnvoller
    Slider möglich ist.

    All-NaN-Spalten liefern min=max=nan — und nan != nan ist True, weshalb
    die einfache Prüfung einen Slider mit NaN-Grenzen durchließe. Konstante
    Spalten (min == max) brauchen ebenfalls keinen Slider.
    """
    _min, _max = float(series.min()), float(series.max())
    if _min != _min or _max != _max:  # NaN-Check ohne math.isnan
        return None
    if _min == _max:
        return None
    return _min, _max


def _render_sidebar_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Daten filtern")

    filtered_df = df.copy()

    search_term = st.sidebar.text_input("Globale Textsuche...")
    if search_term:
        filtered_df = filtered_df[_text_search_mask(filtered_df, search_term)]

    filter_columns = st.sidebar.multiselect("Spalten für Filter auswählen:", df.columns)

    for col in filter_columns:
        if pd.api.types.is_numeric_dtype(filtered_df[col]):
            bounds = _slider_bounds(df[col])
            if bounds is not None:
                _min, _max = bounds
                step = (_max - _min) / 100
                user_num_input = st.sidebar.slider(
                    f"Wertebereich {col}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                filtered_df = filtered_df[filtered_df[col].between(*user_num_input)]

        elif pd.api.types.is_object_dtype(
            filtered_df[col]
        ) or pd.api.types.is_categorical_dtype(filtered_df[col]):
            unique_values = df[col].dropna().unique()
            user_cat_input = st.sidebar.multiselect(
                f"Kategorien {col}", unique_values, default=unique_values
            )
            filtered_df = filtered_df[filtered_df[col].isin(user_cat_input)]

    numeric_df = filtered_df.select_dtypes(include=["number"])
    return filtered_df, numeric_df


def _render_tab1(df: pd.DataFrame, filtered_df: pd.DataFrame, raw_json) -> None:
    st.subheader("Interaktive Datenvorschau & Auswahl")

    with st.expander(" Erkannte Spaltentypen"):
        type_df = (
            pd.DataFrame(df.dtypes.astype(str), columns=["Datentyp"])
            .reset_index()
            .rename(columns={"index": "Spalte"})
        )
        st.dataframe(type_df, use_container_width=True)

    if raw_json is not None:
        with st.expander(" JSON Tree-Ansicht (Hierarchische Navigation)", expanded=True):
            st.json(raw_json)

    st.write(f"Angezeigt: {filtered_df.shape[0]} von {df.shape[0]} Zeilen.")

    event = st.dataframe(
        filtered_df,
        use_container_width=True,
        on_select="rerun",
        selection_mode="multi-row",
    )
    selected_indices = event.selection.rows

    final_selection_df = (
        filtered_df.iloc[selected_indices] if selected_indices else filtered_df
    )
    if selected_indices:
        st.success(f"{len(selected_indices)} Zeilen ausgewählt.")

    st.markdown("---")
    st.subheader("💾 Export & Reports")

    csv_data = df_to_csv_bytes(final_selection_df)
    json_data = final_selection_df.to_json(orient="records", force_ascii=False).encode("utf-8")
    excel_data = df_to_excel_bytes(final_selection_df, sheet_name="Daten")

    def generate_md_report(data: pd.DataFrame) -> str:
        md = "# Automatischer Daten-Report\n\n"
        md += f"**Analysierte Zeilen:** {data.shape[0]}  \n**Analysierte Spalten:** {data.shape[1]}  \n\n"
        md += "## 1. Fehlende Werte\n"
        missing = data.isnull().sum()
        md += (
            missing[missing > 0].to_markdown()
            if missing.sum() > 0
            else "Keine fehlenden Werte.\n"
        )
        md += "\n\n## 2. Deskriptive Statistik\n"
        num_data = data.select_dtypes(include=["number"])
        md += (
            num_data.describe().to_markdown() + "\n\n"
            if not num_data.empty
            else "Keine numerischen Spalten.\n\n"
        )
        md += "## 3. Duplikate\n"
        md += f"Es wurden **{data.astype(str).duplicated().sum()}** doppelte Zeilen gefunden.\n"
        return md

    col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
    with col_ex1:
        st.download_button(" CSV Export", data=csv_data, file_name="daten.csv", mime="text/csv", key="tab_csv")
    with col_ex2:
        st.download_button(
            " Excel Export",
            data=excel_data,
            file_name="daten.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="tab_excel",
        )
    with col_ex3:
        st.download_button(
            " JSON Export",
            data=json_data,
            file_name="daten.json",
            mime="application/json",
            key="tab_json",
        )
    with col_ex4:
        st.download_button(
            " Markdown Report",
            data=generate_md_report(final_selection_df).encode("utf-8"),
            file_name="report.md",
            mime="text/markdown",
            key="tab_md_report",
        )


def _render_tab2(numeric_df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    st.subheader("Mathematische Ausreißer-Erkennung")
    if not numeric_df.empty:
        outlier_report = []
        outlier_data_dict = {}

        for col in numeric_df.columns:
            Q1 = numeric_df[col].quantile(0.25)
            Q3 = numeric_df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR

            outliers = filtered_df[
                (filtered_df[col] < lower) | (filtered_df[col] > upper)
            ]
            outlier_report.append(
                {
                    "Spalte": col,
                    "Q1": Q1,
                    "Q3": Q3,
                    "IQR": IQR,
                    "Unten": lower,
                    "Oben": upper,
                    "Anzahl": len(outliers),
                }
            )

            if len(outliers) > 0:
                outlier_data_dict[col] = outliers

        st.dataframe(
            pd.DataFrame(outlier_report).style.format(precision=2),
            use_container_width=True,
        )

        if outlier_data_dict:
            st.markdown("---")
            st.subheader(" Detailansicht: Die echten Datensätze")

            selected_outlier_col = st.selectbox(
                "Wähle eine Spalte, um die exakten Ausreißer-Zeilen zu analysieren:",
                list(outlier_data_dict.keys()),
            )

            if selected_outlier_col:
                st.write(
                    f"Zeige {len(outlier_data_dict[selected_outlier_col])} gefundene Ausreißer in der Spalte **'{selected_outlier_col}'**:"
                )
                st.dataframe(
                    outlier_data_dict[selected_outlier_col],
                    use_container_width=True,
                )
        else:
            st.success("Perfekt! Es wurden keine Ausreißer in den aktuellen Daten gefunden.")
    else:
        st.warning("Keine numerischen Spalten vorhanden.")


def _render_tab3(numeric_df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    st.subheader("Zusammenhänge visualisieren")
    corr_df = numeric_df.copy()

    smart_encode = st.checkbox(
        " Smart Encode (Binäre Text-Spalten intelligent in 1/0 umwandeln)"
    )

    if smart_encode:
        cat_cols = filtered_df.select_dtypes(include=["object", "category"]).columns
        encoded_cols = []

        pos_terms = ["yes", "ja", "true", "wahr", "m", "male"]
        neg_terms = ["no", "nein", "false", "f", "female"]

        for col in cat_cols:
            unique_vals = filtered_df[col].dropna().unique()
            if len(unique_vals) == 2:
                val1, val2 = unique_vals[0], unique_vals[1]
                str1, str2 = str(val1).lower(), str(val2).lower()

                if str1 in pos_terms or str2 in neg_terms:
                    mapping = {val1: 1, val2: 0}
                elif str2 in pos_terms or str1 in neg_terms:
                    mapping = {val1: 0, val2: 1}
                else:
                    sorted_vals = sorted([val1, val2])
                    mapping = {sorted_vals[0]: 0, sorted_vals[1]: 1}

                corr_df[col] = filtered_df[col].map(mapping)
                val_for_1 = val1 if mapping[val1] == 1 else val2
                encoded_cols.append(f"'{col}' ({val_for_1} = 1)")

        if encoded_cols:
            st.success(f"Erfolgreich codiert: {', '.join(encoded_cols)}")
        else:
            st.info("Keine passenden binären Text-Spalten gefunden.")

    if len(corr_df.columns) > 1:
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.heatmap(corr_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
        st.pyplot(fig)
    else:
        st.warning("Mindestens zwei numerische (oder codierte) Spalten benötigt.")


def _render_tab4(filtered_df: pd.DataFrame, numeric_df: pd.DataFrame) -> None:
    st.subheader(" Berechnungsbausteine & Qualitäts-Checks")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(" Deskriptive Statistik"):
            if not numeric_df.empty:
                st.write("**Statistische Kennzahlen:**")
                st.dataframe(numeric_df.describe(), use_container_width=True)
            else:
                st.info("Keine numerischen Daten.")

    with col2:
        if st.button(" Missing-Value-Report"):
            missing = filtered_df.isnull().sum()
            if missing.sum() > 0:
                st.dataframe(missing[missing > 0].rename("Anzahl fehlend"))
                fig, ax = plt.subplots(figsize=(6, 4))
                sns.heatmap(
                    filtered_df.isnull(),
                    cbar=False,
                    cmap="viridis",
                    yticklabels=False,
                    ax=ax,
                )
                st.pyplot(fig)

                cat_cols = filtered_df.select_dtypes(include=["object", "category"]).columns
                if len(cat_cols) > 0:
                    group_col = cat_cols[0]
                    st.write(f"**Missing-Rate (%) gruppiert nach '{group_col}':**")
                    missing_rates = filtered_df.groupby(group_col).apply(
                        lambda x: x.isnull().mean() * 100
                    )
                    st.dataframe(
                        missing_rates[missing[missing > 0].index].style.format("{:.1f}%"),
                        use_container_width=True,
                    )
            else:
                st.success("Keine fehlenden Werte gefunden.")

    with col3:
        if st.button("👯 Duplikat-Check"):
            dups = filtered_df.astype(str).duplicated().sum()
            if dups > 0:
                st.warning(f"{dups} doppelte Zeilen gefunden! Hier sind alle Einträge dazu:")
                duplicate_mask = filtered_df.astype(str).duplicated(keep=False)
                st.dataframe(filtered_df[duplicate_mask], use_container_width=True)
            else:
                st.success("Keine Duplikate gefunden!")

    st.markdown("---")
    col4, col5, col6 = st.columns(3)

    with col4:
        if st.button("Value Counts"):
            cat_cols = filtered_df.select_dtypes(include=["object", "category"]).columns
            if len(cat_cols) > 0:
                for col in cat_cols:
                    st.write(f"**Top Werte in '{col}':**")
                    st.dataframe(_safe_value_counts(filtered_df[col]).head(5))
            else:
                st.info("Keine Text-Spalten vorhanden.")

    with col5:
        variance_threshold = st.slider(
            "Schwellenwert (%) für konstante Werte",
            min_value=50,
            max_value=100,
            value=95,
        )
        if st.button("Konstante Spalten (Variance Check)"):
            quasi_constant_cols = []
            total_rows = len(filtered_df)
            if total_rows > 0:
                for col in filtered_df.columns:
                    max_freq = _safe_value_counts(filtered_df[col], dropna=False).max()

                    if (max_freq / total_rows) * 100 >= variance_threshold:
                        quasi_constant_cols.append(col)

            if quasi_constant_cols:
                st.warning(
                    f"Quasi-konstant (≥{variance_threshold}% gleicher Wert): {', '.join(quasi_constant_cols)}"
                )
            else:
                st.success(
                    f"Alle Spalten haben genug Varianz (<{variance_threshold}% gleiche Werte)."
                )

    with col6:
        if st.button("Typenkonflikte"):
            conflicts = []
            for col in filtered_df.columns:
                if pd.api.types.is_object_dtype(filtered_df[col]):
                    valid_vals = filtered_df[col].dropna()
                    if not valid_vals.empty:
                        num_test = pd.to_numeric(valid_vals, errors="coerce")
                        if num_test.notna().sum() / len(valid_vals) > 0.8:
                            conflicts.append(col)

            if conflicts:
                st.warning(
                    f" Typkonflikt (Text enthält heimlich Zahlen):\n**{', '.join(conflicts)}**"
                )
            else:
                st.success("Sauber! Keine Zahlen als Text getarnt.")


def render_tabular_section(df: pd.DataFrame, raw_json) -> None:
    filtered_df, numeric_df = _render_sidebar_filters(df)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            " Datenansicht & Export",
            "🔍 Ausreißer (IQR)",
            " Korrelationen",
            " Daten-Qualität",
        ]
    )

    with tab1:
        _render_tab1(df, filtered_df, raw_json)
    with tab2:
        _render_tab2(numeric_df, filtered_df)
    with tab3:
        _render_tab3(numeric_df, filtered_df)
    with tab4:
        _render_tab4(filtered_df, numeric_df)
