# Projektstatus

---

## AP1 – Bestehende App modularisieren ✅ ABGESCHLOSSEN

### Was wurde gemacht

`app.py` (509 Zeilen, monolithisch) wurde in klar getrennte Module zerlegt. Die gesamte bestehende Funktionalität bleibt erhalten.

### Neue Dateistruktur

```
src/
├── __init__.py
├── session.py                       ← zentrale Datenverwaltung (st.session_state)
├── loaders/
│   ├── __init__.py
│   └── tabular_loader.py        ← load_data() mit @st.cache_data
├── models/
│   └── __init__.py              ← bereit für AP3 (DatasetRecord etc.)
├── preprocessing/
│   └── __init__.py              ← bereit für AP5/AP7
├── analysis/
│   └── __init__.py              ← bereit für AP10
├── feature_engineering/
│   └── __init__.py              ← bereit für sensor_features.py / web_features.py
└── ui/
    ├── __init__.py
    └── tabular_tab.py           ← alle 4 Tabs + Sidebar-Filter
```

### Verantwortlichkeiten nach Modul

| Datei | Inhalt |
|---|---|
| `app.py` (36 Zeilen) | Page-Config, Sidebar-Uploader, Dispatch — nur Entry-Point |
| `src/loaders/tabular_loader.py` | `load_data(file) → DataFrame` — CSV / Excel / JSON |
| `src/ui/tabular_tab.py` | `render_tabular_section(df, raw_json)` + private Render-Funktionen |

### Öffentliche API von `tabular_tab.py`

```python
render_tabular_section(df: pd.DataFrame, raw_json) -> None
```

Intern aufgeteilt in:

- `_render_sidebar_filters(df)` → `(filtered_df, numeric_df)`
- `_render_tab1(df, filtered_df, raw_json)` — Datenansicht & Export
- `_render_tab2(numeric_df, filtered_df)` — Ausreißer (IQR)
- `_render_tab3(numeric_df, filtered_df)` — Korrelationen & Smart Encode
- `_render_tab4(filtered_df, numeric_df)` — Datenqualität

### Zentrale Datenverwaltung – `src/session.py`

Drei Slots, erweiterbar ohne Umbau:

| Funktion | Slot | Verfügbar ab |
|---|---|---|
| `set_tabular / get_tabular / has_tabular` | `tabular_df`, `tabular_raw_json` | AP1 ✅ |
| `add_trial / get_trials / has_trials` | `trials: list` | AP4 |
| `add_website / get_websites / has_websites` | `websites: list` | AP9 |

---

---

## AP3 – Gemeinsames internes Datenmodell ✅ ABGESCHLOSSEN

| Datei | Modelle |
|---|---|
| `src/models/records.py` | `DatasetRecord` |
| `src/models/experiment_records.py` | `EventRecord`, `EventType`, `SensorStreamRecord`, `TrialRecord`, `WindowDefinition`, `WindowFeatureRecord` |
| `src/models/web_records.py` | `PageRecord`, `WebsiteRecord` |

`SensorStreamRecord.channels` ist ein offenes `dict[str, list]` — neue Sensorquellen (OpenBCI, IMU, …) werden als zusätzliche Keys eingehängt, ohne das Modell zu ändern.

`src/session.py` ist jetzt vollständig typisiert: `add_trial(TrialRecord)`, `add_website(WebsiteRecord)`.

---

## Offene Arbeitspakete

| AP | Titel | Status |
|---|---|---|
| AP3 | Gemeinsames internes Datenmodell | ✅ abgeschlossen |
| AP4 | Flexible Importschicht (Trials & Websites) | ✅ abgeschlossen |
| AP5 | Task- und Segmentlogik für Experimente | ✅ abgeschlossen |
| AP6 | Zeitfenster-Manager | ✅ abgeschlossen |
| AP7 | Sensorfusion und zeitliche Verdichtung | ✅ abgeschlossen |
| AP8 | Qualitätsprüfungen für multimodale Daten | ✅ abgeschlossen |
| AP9 | Webcrawler-Modul integrieren | ✅ abgeschlossen |
| AP10 | Analysen für Webdaten | ✅ abgeschlossen |
| AP11 | Neue Tabs in der Oberfläche | ✅ abgeschlossen |
| AP12 | Export- und Reporting-Funktionen | ✅ abgeschlossen |
| AP13 | Optionales ML-Modul | ⬜ niedrige Prio |
