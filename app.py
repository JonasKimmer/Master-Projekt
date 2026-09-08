import json

import streamlit as st

from src.loaders.tabular_loader import is_json_file, load_data
from src.session import get_tabular, has_tabular, set_tabular
from src.ui.import_tab import render_import_tab
from src.ui.inventory_tab import render_inventory_tab
from src.ui.ml_tab import render_ml_tab
from src.ui.reporting_tab import render_reporting_tab
from src.ui.styles import inject_styles
from src.ui.tabular_tab import render_tabular_section
from src.ui.trials_tab import render_trials_tab
from src.ui.website_tab import render_website_tab
from src.ui.windows_tab import render_windows_tab

st.set_page_config(
    page_title="Data Discovery Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()

st.markdown(
    "<h1>📊 Data Discovery Tool</h1>"
    "<p style='color:#6B7280;font-size:0.95rem;margin-top:-0.5rem;'>"
    "Multimodale Exploration · Tabellarische Daten · Experiment-Trials · Webcrawler-Daten"
    "</p><hr style='margin:1rem 0 1.5rem 0;'>",
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Tabellarische Daten")
    uploaded_file = st.file_uploader("Datei hochladen", type=["csv", "xlsx", "json"])
    st.info("CSV, Excel, JSON")

    st.markdown("---")
    dark_mode = st.toggle("Dark Mode", value=False, key="dark_mode")
    if dark_mode:
        st.markdown(
            """<style>
            .stApp { background-color: #0F1117 !important; color: #FAFAFA !important; }
            .block-container { background-color: #0F1117 !important; }
            h1, h2, h3, p, label, span { color: #FAFAFA !important; }
            [data-testid="stSidebar"] { background-color: #1A1D2E !important; border-right: 1px solid #2D3148 !important; }
            .stTabs [data-baseweb="tab-list"] { background-color: #1A1D2E !important; }
            .stTabs [aria-selected="true"] { background-color: #2D3148 !important; color: #818CF8 !important; }
            .stTabs [data-baseweb="tab"] { color: #9CA3AF !important; }
            [data-testid="stMetric"] { background-color: #1A1D2E !important; border-color: #2D3148 !important; }
            [data-testid="stDataFrame"] { border-color: #2D3148 !important; }
            [data-testid="stExpander"] { background-color: #1A1D2E !important; border-color: #2D3148 !important; }
            hr { border-color: #2D3148 !important; }
            </style>""",
            unsafe_allow_html=True,
        )

@st.cache_data
def _parse_raw_json(raw_bytes: bytes) -> object:
    return json.loads(raw_bytes)


if uploaded_file is not None:
    raw_json = _parse_raw_json(uploaded_file.getvalue()) if is_json_file(uploaded_file) else None
    df = load_data(uploaded_file)
    set_tabular(df, raw_json, source_name=uploaded_file.name)

# ── Main tabs ─────────────────────────────────────────────────────────────────
(tab_tabular, tab_import, tab_inventory,
 tab_trials, tab_windows, tab_websites,
 tab_reporting, tab_ml) = st.tabs([
    "Tabellarische Daten",
    "Import",
    "Dateninventar",
    "Trials",
    "Zeitfenster",
    "Websites",
    "Reporting",
    "ML",
])

with tab_tabular:
    if has_tabular():
        df, raw_json = get_tabular()
        render_tabular_section(df, raw_json)
    else:
        st.info("Bitte lade zuerst eine Datei über die Sidebar hoch.")

with tab_import:
    render_import_tab()

with tab_inventory:
    render_inventory_tab()

with tab_trials:
    render_trials_tab()

with tab_windows:
    render_windows_tab()

with tab_websites:
    render_website_tab()

with tab_reporting:
    render_reporting_tab()

with tab_ml:
    render_ml_tab()
