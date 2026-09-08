"""
Central session state for all data sources.

Slots:
  tabular  – uploaded CSV/Excel/JSON (AP1)
  trials   – list of TrialRecord objects (AP4)
  websites – list of WebsiteRecord objects (AP9)
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.models.experiment_records import TrialRecord
from src.models.records import DatasetRecord
from src.models.web_records import WebsiteRecord

_DEFAULT_FACTORIES: dict[str, Any] = {
    "tabular_df": lambda: None,
    "tabular_raw_json": lambda: None,
    "tabular_record": lambda: None,
    "trials": list,
    "websites": list,
}


def _init() -> None:
    for key, factory in _DEFAULT_FACTORIES.items():
        if key not in st.session_state:
            st.session_state[key] = factory()


# ── Tabular ──────────────────────────────────────────────────────────────────

def set_tabular(df: pd.DataFrame, raw_json: Any = None, source_name: str = "") -> None:
    _init()
    st.session_state.tabular_df = df
    st.session_state.tabular_raw_json = raw_json
    # DatasetRecord als typisierte Beschreibung des Uploads (AP3-Modell,
    # DataFrame bleibt separat im Session-State wegen Serialisierung)
    st.session_state.tabular_record = DatasetRecord(
        name=source_name or "upload",
        meta={
            "n_rows": int(df.shape[0]),
            "n_cols": int(df.shape[1]),
            "columns": list(df.columns),
            "has_raw_json": raw_json is not None,
        },
    )


def get_tabular_record() -> DatasetRecord | None:
    _init()
    return st.session_state.tabular_record


def get_tabular() -> tuple[pd.DataFrame | None, Any]:
    _init()
    return st.session_state.tabular_df, st.session_state.tabular_raw_json


def has_tabular() -> bool:
    _init()
    return st.session_state.tabular_df is not None


# ── Trials (AP4) ─────────────────────────────────────────────────────────────

def get_trials() -> list[TrialRecord]:
    _init()
    return st.session_state.trials


def add_trial(trial: TrialRecord) -> None:
    _init()
    st.session_state.trials.append(trial)


def has_trials() -> bool:
    _init()
    return len(st.session_state.trials) > 0


# ── Websites (AP9) ────────────────────────────────────────────────────────────

def get_websites() -> list[WebsiteRecord]:
    _init()
    return st.session_state.websites


def add_website(website: WebsiteRecord) -> None:
    _init()
    st.session_state.websites.append(website)


def has_websites() -> bool:
    _init()
    return len(st.session_state.websites) > 0
