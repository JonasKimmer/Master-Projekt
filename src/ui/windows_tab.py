"""AP11 – Windows tab: configure time windows and compute sensor features.

AP6: Fensterdefinitionen sind versionierbar speicher- und ladbbar
     (WindowDefinitionStore, Persistenz in window_definitions.json).
AP7: Der Stream kann vor der Fensterung auf ein einheitliches Zeitraster
     synchronisiert (resampled) werden.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analysis.reporting import window_features_to_dataframe
from src.analysis.statistics import notable_windows
from src.models.experiment_records import WindowDefinition, WindowFeatureRecord
from src.preprocessing.segmentation import build_timeline_from_trial
from src.preprocessing.synchronization import split_fusion_stream, resample_stream
from src.preprocessing.window_store import WindowDefinitionStore
from src.preprocessing.windowing import generate_windows, slice_stream
from src.feature_engineering.sensor_features import compute_window_features
from src.session import get_trials


def _select_stream(trial):
    """Stream-Auswahl inkl. optionaler modality-Splits (ohne Prefix-Dopplung)."""
    options: list[tuple[str, object]] = []
    for s in trial.streams:
        options.append((f"{s.source} (fusion, komplett)", s))
        for part in split_fusion_stream(s):
            if part.timestamps:
                options.append((f"{s.source} → {part.modality}", part))
    return options


def render_windows_tab() -> None:
    trials = get_trials()
    if not trials:
        st.info("Keine Trials geladen. → Tab 'Import'")
        return

    # Gespeicherte Definition anwenden, BEVOR die Widgets erzeugt werden:
    # Widget-gebundene Session-State-Keys dürfen nur vor der Instanziierung
    # des Widgets gesetzt werden, sonst wirft Streamlit eine
    # StreamlitAPIException. Der Load-Button setzt daher nur ein Flag
    # (_win_pending_load) und löst einen Rerun aus; hier wird es angewandt.
    pending_id = st.session_state.pop("_win_pending_load", None)
    if pending_id is not None:
        loaded = WindowDefinitionStore().load(pending_id)
        if loaded is not None:
            st.session_state.win_mode = loaded.mode
            st.session_state.win_duration = int(loaded.duration_ms)
            st.session_state.win_step = int(loaded.step_ms) if loaded.step_ms else 1000
            st.session_state.win_offset_start = int(loaded.offset_start_ms)
            st.session_state.win_offset_end = int(loaded.offset_end_ms)
            if loaded.mode == "task" and loaded.task_label:
                # Task-Label erst validieren, wenn die Segment-Optionen des
                # aktuell gewählten Trials bekannt sind (siehe Task-Modus).
                label = loaded.task_label
                if loaded.task_domain:
                    label = f"{label} [{loaded.task_domain}]"
                st.session_state["_win_pending_task_label"] = label
            else:
                # Fixed-/Sliding-Definition: veraltete Task-Auswahl
                # zurücksetzen, damit der Task-Modus später nicht einem
                # längst geladenen Label folgt.
                st.session_state.pop("win_task_label", None)
                st.session_state.pop("_win_pending_task_label", None)
                st.session_state.pop("_win_task_label_trial", None)
            st.info(
                f"Definition '{loaded.window_id}' geladen "
                f"(Modus {loaded.mode}, {int(loaded.duration_ms)} ms)."
            )

    st.subheader("Zeitfenster-Manager")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### Konfiguration")
        trial_id = st.selectbox("Trial", [t.trial_id for t in trials], key="win_trial")
        trial = next(t for t in trials if t.trial_id == trial_id)

        stream_options = _select_stream(trial)
        if not stream_options:
            st.warning("Kein Stream vorhanden.")
            return
        labels = [lbl for lbl, _ in stream_options]
        stream_src = st.selectbox("Stream", labels, key="win_stream")
        stream = next(s for lbl, s in stream_options if lbl == stream_src)

        # AP7 – Synchronisation auf einheitliches Raster
        st.markdown("**Synchronisation (AP7)**")
        do_sync = st.checkbox(
            "Auf einheitliches Zeitraster resampeln",
            value=False,
            help="Linear-Interpolation auf ein gemeinsames Abtastraster (AP7: Zeitstempel synchronisieren).",
            key="win_sync",
        )
        if do_sync:
            sync_hz = st.number_input(
                "Ziel-Abtastrate (Hz)", min_value=1, value=10, step=1, key="win_sync_hz"
            )
            stream = resample_stream(stream, float(sync_hz))

        mode = st.radio("Modus", ["sliding", "fixed", "task"], key="win_mode")
        duration = st.number_input("Fensterlänge (ms)", min_value=100, value=2000, step=100, key="win_duration")

        step = None
        task_label = None
        task_domain = None
        task_timeline = None
        if mode == "sliding":
            step = st.number_input("Schrittweite (ms)", min_value=100, value=1000, step=100, key="win_step")
        elif mode == "task":
            task_timeline = build_timeline_from_trial(trial)
            # Segmente als "label [domain]" anbieten — Domain-Info aus Event-Meta
            seg_options = sorted({
                (s.label, s.domain or "") for s in task_timeline.segments
            })
            if seg_options:
                option_labels = [f"{lbl} [{dom}]" if dom else lbl
                                 for lbl, dom in seg_options]
                # Stale Task-Auswahl beim Trial-Wechsel zurücksetzen — nicht
                # nur bei gespeicherten Definitionen: das Label des vorher
                # gewählten Trials kann für den neuen ungültig (nicht in
                # option_labels) oder schlicht falsch sein. Der Marker merkt
                # sich, für welchen Trial die aktuelle Auswahl gilt.
                if st.session_state.get("_win_task_label_trial") != trial_id:
                    st.session_state.pop("win_task_label", None)
                    st.session_state["_win_task_label_trial"] = trial_id
                # Gespeichertes Task-Label validieren: existiert es im
                # aktuell gewählten Trial überhaupt? Sonst zurücksetzen.
                pending_label = st.session_state.pop("_win_pending_task_label", None)
                if pending_label is not None:
                    if pending_label in option_labels:
                        st.session_state.win_task_label = pending_label
                        st.session_state["_win_task_label_trial"] = trial_id
                    else:
                        st.session_state.pop("win_task_label", None)
                        st.info(
                            f"Gespeichertes Task-Label '{pending_label}' kommt "
                            "im gewählten Trial nicht vor — Auswahl zurückgesetzt."
                        )
                sel = st.selectbox(
                    "Task-Label",
                    option_labels,
                    key="win_task_label",
                )
                task_label, _, dom_part = sel.partition(" [")
                task_domain = dom_part.rstrip("]") or None
            else:
                st.warning("Trial hat keine Segmente (keine Events oder keine erkennbaren Start/End-Paare) — Task-Modus benötigt Event-Daten.")

        offset_start = st.number_input("Offset Start (ms)", value=0, step=100, key="win_offset_start")
        offset_end   = st.number_input("Offset Ende (ms)", value=0, step=100, key="win_offset_end")

        # ── AP6: versionierbares Speichern / Laden ─────────────────────────────
        st.markdown("**Definition versionierbar speichern (AP6)**")
        store = WindowDefinitionStore()
        def_name = st.text_input(
            "Name der Definition", placeholder="z. B. baseline_2s", key="win_def_name"
        )
        if st.button("Aktuelle Konfiguration speichern", key="win_def_save"):
            try:
                definition = WindowDefinition(
                    window_id=def_name or "manual",
                    mode=mode,
                    duration_ms=float(duration),
                    step_ms=float(step) if step else None,
                    task_label=task_label,
                    task_domain=task_domain,
                    offset_start_ms=float(offset_start),
                    offset_end_ms=float(offset_end),
                )
                entry = store.save(def_name, definition)
                st.success(f"Gespeichert: '{entry['name']}' v{entry['version']} (id {entry['id']}).")
            except ValueError as e:
                st.error(str(e))

        entries = store.list_entries()
        if entries:
            entry_labels = {
                f"#{e['id']} {e['name']} v{e['version']} ({e['created_at']})": e["id"]
                for e in entries
            }
            sel_entry = st.selectbox("Gespeicherte Definitionen", list(entry_labels), key="win_def_sel")
            if st.button("Definition laden", key="win_def_load"):
                # Nur Flag setzen + Rerun — angewandt wird die Definition am
                # Anfang des nächsten Runs, bevor die Widgets existieren.
                st.session_state["_win_pending_load"] = entry_labels[sel_entry]
                st.rerun()

    with col2:
        st.markdown("#### Ergebnisse")
        compute = st.button("Fenster berechnen", key="win_compute")
        if compute:
            definition = WindowDefinition(
                window_id=def_name or "manual",
                mode=mode,
                duration_ms=float(duration),
                step_ms=float(step) if step else None,
                task_label=task_label,
                task_domain=task_domain,
                offset_start_ms=float(offset_start),
                offset_end_ms=float(offset_end),
            )
            try:
                windows = generate_windows(stream, definition, task_timeline)
            except ValueError as e:
                st.error(f"Ungültige Fensterdefinition: {e}")
                windows = []

            if not windows:
                st.warning("Keine Fenster generiert.")
            else:
                st.info(f"{len(windows)} Fenster generiert.")
                # WindowFeatureRecord je Fenster — das zentrale Modell (AP3),
                # Export über reporting.window_features_to_dataframe
                records: list[WindowFeatureRecord] = []
                all_rows = []
                for i, (start, end) in enumerate(windows):
                    sliced = slice_stream(stream, start, end)
                    feats = compute_window_features(sliced)
                    if feats:
                        records.append(WindowFeatureRecord(
                            window_id=definition.window_id,
                            trial_id=trial_id,
                            modality=stream.modality,
                            start_ms=start,
                            end_ms=end,
                            features=feats,
                        ))
                    for ch, ch_feats in feats.items():
                        row = {"window": i, "start_ms": round(start), "end_ms": round(end), "channel": ch}
                        row.update(ch_feats)
                        all_rows.append(row)

                if all_rows:
                    df = pd.DataFrame(all_rows)
                    st.dataframe(df, use_container_width=True)

                    # Auffällige Fenster direkt im Tool (kein ML-Umweg nötig)
                    flagged = notable_windows(df)
                    if not flagged.empty:
                        st.warning(f"{len(flagged)} auffällige Fenster-Merkmale erkannt:")
                        st.dataframe(flagged, use_container_width=True)
                        df = df.merge(
                            flagged[["window", "channel", "reason"]],
                            on=["window", "channel"], how="left",
                        )
                        df["reason"] = df["reason"].fillna("")

                    # Breite Feature-Tabelle (eine Zeile pro Fenster) für
                    # nachgelagerte Statistik / ML exportieren
                    df_wide = window_features_to_dataframe(records)
                    dl1, dl2 = st.columns(2)
                    with dl1:
                        st.download_button(
                            "Features CSV (lang, mit Flags)",
                            data=df.to_csv(index=False).encode(),
                            file_name=f"{trial_id}_windows.csv",
                            mime="text/csv",
                            key=f"win_features_csv_{trial_id}",
                        )
                    with dl2:
                        st.download_button(
                            "Features CSV (breit, 1 Zeile/Fenster)",
                            data=df_wide.to_csv(index=False).encode(),
                            file_name=f"{trial_id}_windows_wide.csv",
                            mime="text/csv",
                            key=f"win_features_wide_csv_{trial_id}",
                        )
                else:
                    st.warning("Keine numerischen Merkmale berechenbar.")
