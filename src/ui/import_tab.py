"""AP11 – Import tab: load trial and website folders into session state."""

from __future__ import annotations

from typing import Callable, TypeVar

import streamlit as st

from src.loaders.trial_loader import load_trials_from_dir
from src.loaders.website_loader import load_websites_from_dir
from src.session import add_trial, add_website, get_trials, get_websites

T = TypeVar("T")


def _render_folder_import(
    *,
    label: str,
    dir_key: str,
    load_fn: Callable[[str], list[T]],
    get_existing_fn: Callable[[], list[T]],
    add_fn: Callable[[T], None],
    id_attr: str,
    not_found_msg: str,
) -> None:
    st.markdown(f"#### {label}")
    folder = st.text_input(
        "Pfad zum Ordner",
        placeholder="/pfad/zu/ordner/",
        key=f"{dir_key}_input",
    )
    if st.button(f"{label} laden", key=f"{dir_key}_btn"):
        if not folder:
            st.warning("Bitte einen Ordnerpfad eingeben.")
        else:
            try:
                with st.spinner(f"Lade {label}…"):
                    loaded = load_fn(folder)
                if not loaded:
                    st.warning(not_found_msg)
                else:
                    existing_ids = {getattr(item, id_attr) for item in get_existing_fn()}
                    new = [item for item in loaded if getattr(item, id_attr) not in existing_ids]
                    for item in new:
                        add_fn(item)
                    st.success(f"{len(new)} geladen, {len(loaded) - len(new)} bereits vorhanden.")
            except Exception as e:
                st.error(f"Fehler: {e}")

    existing = get_existing_fn()
    if existing:
        st.caption(f"{len(existing)} im Speicher: {', '.join(getattr(item, id_attr) for item in existing)}")


def render_import_tab() -> None:
    st.subheader("Multimodale Daten importieren")

    col1, col2 = st.columns(2)

    with col1:
        _render_folder_import(
            label="Experiment-Trials",
            dir_key="trials_dir",
            load_fn=load_trials_from_dir,
            get_existing_fn=get_trials,
            add_fn=add_trial,
            id_attr="trial_id",
            not_found_msg="Keine Trial-Ordner gefunden.",
        )

    with col2:
        _render_folder_import(
            label="Webcrawler-Daten",
            dir_key="websites_dir",
            load_fn=load_websites_from_dir,
            get_existing_fn=get_websites,
            add_fn=add_website,
            id_attr="website_id",
            not_found_msg="Keine Website-Ordner gefunden.",
        )
