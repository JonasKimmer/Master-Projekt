"""Global CSS styles injected once at app startup."""

import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        /* ── Fonts & Base ─────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* ── Page background ──────────────────────────────────────── */
        .stApp {
            background-color: #F8F9FC;
        }

        /* ── Main content padding ─────────────────────────────────── */
        .block-container {
            padding: 2rem 2.5rem 3rem 2.5rem !important;
            max-width: 1400px;
        }

        /* ── Title ────────────────────────────────────────────────── */
        h1 {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: #1A1D2E !important;
            letter-spacing: -0.5px;
            margin-bottom: 0.2rem !important;
        }

        /* ── Subheaders ───────────────────────────────────────────── */
        h2, h3 {
            font-weight: 600 !important;
            color: #1A1D2E !important;
        }

        /* ── Subtitle text ────────────────────────────────────────── */
        .stApp > div > div > div > div > p:first-of-type {
            color: #6B7280;
            font-size: 0.95rem;
        }

        /* ── Tabs ─────────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0px;
            background-color: #ECEEF5;
            border-radius: 12px;
            padding: 4px;
            border: none;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 9px;
            padding: 8px 18px;
            font-weight: 500;
            font-size: 0.88rem;
            color: #6B7280;
            border: none;
            background: transparent;
        }

        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #4F6EF7 !important;
            font-weight: 600 !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.10) !important;
        }

        /* ── Sidebar ──────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #E5E7EB;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            font-size: 0.95rem !important;
            color: #374151 !important;
            font-weight: 600 !important;
        }

        /* ── Metric cards ─────────────────────────────────────────── */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
            color: #6B7280 !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            color: #1A1D2E !important;
        }

        /* ── Buttons ──────────────────────────────────────────────── */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.88rem !important;
            padding: 0.45rem 1.1rem !important;
            border: 1.5px solid #4F6EF7 !important;
            color: #4F6EF7 !important;
            background: transparent !important;
            transition: all 0.15s ease;
        }

        .stButton > button:hover {
            background: #4F6EF7 !important;
            color: #ffffff !important;
        }

        /* ── Download buttons ─────────────────────────────────────── */
        [data-testid="stDownloadButton"] > button {
            border-radius: 8px !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            background-color: #F3F4F6 !important;
            color: #374151 !important;
            border: 1px solid #E5E7EB !important;
            padding: 0.4rem 0.9rem !important;
        }

        [data-testid="stDownloadButton"] > button:hover {
            background-color: #4F6EF7 !important;
            color: #ffffff !important;
            border-color: #4F6EF7 !important;
        }

        /* ── Dataframes ───────────────────────────────────────────── */
        [data-testid="stDataFrame"] {
            border-radius: 10px !important;
            overflow: hidden;
            border: 1px solid #E5E7EB !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }

        /* ── Info / Success / Warning boxes ──────────────────────── */
        [data-testid="stAlert"] {
            border-radius: 10px !important;
            font-size: 0.88rem !important;
        }

        /* ── Expanders ────────────────────────────────────────────── */
        [data-testid="stExpander"] {
            border: 1px solid #E5E7EB !important;
            border-radius: 10px !important;
            background: #ffffff !important;
        }

        /* ── Select / Input fields ────────────────────────────────── */
        [data-testid="stSelectbox"] > div > div,
        [data-testid="stTextInput"] > div > div > input {
            border-radius: 8px !important;
            border: 1px solid #D1D5DB !important;
            font-size: 0.88rem !important;
        }

        /* ── Divider ──────────────────────────────────────────────── */
        hr {
            border: none;
            border-top: 1px solid #E5E7EB;
            margin: 1.5rem 0;
        }

        /* ── Caption / small text ─────────────────────────────────── */
        .stCaption, small {
            color: #9CA3AF !important;
            font-size: 0.78rem !important;
        }

        /* ── File uploader ────────────────────────────────────────── */
        [data-testid="stFileUploader"] {
            border-radius: 10px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
