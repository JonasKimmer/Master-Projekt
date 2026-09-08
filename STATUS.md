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

## Arbeitspakete — Gesamtstand

| AP | Titel | Status |
|---|---|---|
| AP1 | Bestehende App modularisieren | ✅ abgeschlossen |
| AP3 | Gemeinsames internes Datenmodell | ✅ abgeschlossen |
| AP4 | Flexible Importschicht (Trials & Websites) | ✅ abgeschlossen |
| AP5 | Task- und Segmentlogik für Experimente | ✅ abgeschlossen |
| AP6 | Zeitfenster-Manager (versionierbar, AP6-Store) | ✅ abgeschlossen |
| AP7 | Sensorfusion und zeitliche Verdichtung | ✅ abgeschlossen |
| AP8 | Qualitätsprüfungen für multimodale Daten | ✅ abgeschlossen |
| AP9 | Webcrawler-Modul integriert (`mini_crawler.py`, robots.txt-konform) | ✅ abgeschlossen |
| AP10 | Analysen für Webdaten | ✅ abgeschlossen |
| AP11 | Tabs der Oberfläche (Import · Inventar · Tabellarisch · Trials · Zeitfenster · Websites · Reporting · ML) | ✅ abgeschlossen |
| AP12 | Export- und Reporting-Funktionen (CSV/Excel/JSON/Markdown) | ✅ abgeschlossen |
| AP13 | Optionales ML-Modul (`src/ui/ml_tab.py`, `src/analysis/ml_analysis.py`) | ✅ umgesetzt (KMeans · IsolationForest · RandomForest-Klassifikation/-Regression) |

Alle Arbeitspakete des Projektplans sind umgesetzt; Details zu AP1 und AP3 siehe oben.

---

## Papers und Analyse-Skripte

Beide im Projektplan geforderten ~10-Seiten-Papers liegen vor und sind
mehrfach reviewt (Code, Paper-Inhalt, Reproduzierbarkeit):

- **`paper_1_kognitive_last.md`** — Kognitive Beanspruchung bei der
  Exploration interaktiver Datenvisualisierungen. Alle Kennzahlen
  reproduzierbar über `check_correlations.py` (Korrelationen, Abbildung 2,
  Dauern je Aufgabenposition), `check_mixed_model.py` (Zentrierung,
  personen-geclusterter Bootstrap, MixedLM) und `check_sensor_deltas.py`
  (baseline-zentrierte Sensor-Deltas, Tabelle 4/5, Messraten). Benötigt
  lokale `data/` (Datenschutz, s. Verfügbarkeitsstatement im Paper).
- **`paper_2_webkomplexitaet.md`** — Strukturelle Webkomplexität gecrawlter
  Webseiten. Vollständig aus dem Repo reproduzierbar über
  `check_web_analysis.py` (Tabellen 1–6, k-Scan, Baseline,
  Dekorrelations-Analyse, Feature-Importance, CV/Split, Bootstrap,
  Cluster-Stabilität, beide Abbildungen; dokumentierte Seeds). Nicht
  reproduzierbar: HTTP-Antwortzeit-Tabellen 7/8 (Messdaten nicht archiviert,
  im Paper gekennzeichnet).

---

## Tests und Qualitätssicherung

- `tests/` — 105 Tests, clean-clone-fähig (Real-Data-Test überspringt sich
  ohne `data/` selbst). Abgedeckt: Synchronisation, Segmentierung,
  Trial-/Alias-Verträge, Quality-Checks, ML-Vertragskern, UI-Pfade
  (Tabular-Filter, Missing-Report, Windows-Tab/Definitionsladen) sowie
  alle vier Analyse-Skripte (inkl. Determinismus).
- Neun Review-Runden über Code und Papers; alle gefundenen Crash-Bugs
  behoben, letzte offene Punkte siehe unten.

---

## Verbleibende Punkte (nice-to-have, nicht abgabe-blockierend)

- Testabdeckung für `windowing`, `sensor_features`, `web_features`,
  `reporting` und die ungetesteten Loader (`website_loader`,
  `tabular_loader`) — betrifft App-Pfade, nicht die Paper-Ergebnisse
- pandas-4-Migration: `pd.api.types.is_categorical_dtype` in
  `tabular_tab.py` ist deprecated (löst Warnung aus, Aufruf funktioniert noch)
- Paper 2, optional: StratifiedKFold-/Log-Transform-Robustheitsvarianten
  und balancierte Klassifikationsmetriken nachreichen
- Paper 1: kein erzeugendes Skript für Abbildung 1 (`figures/
  paper1_abb1_tlx_boxplot.png`) — im Paper nicht als reproduzierbar
  deklariert
- Repo-Hygiene: verwaiste `worktree-agent-*`-Branches, `figures/old/`,
  `app.md` (veraltete Plan-Kopie)
