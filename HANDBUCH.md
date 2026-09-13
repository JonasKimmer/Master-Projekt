# Handbuch: Data Discovery Tool

**Multimodale Analyseumgebung für tabellarische Daten, Experiment-Trials (Eye-Tracking + Physiologie) und Webcrawler-Daten.**

Dieses Handbuch beschreibt Installation, Datenformate, alle Funktionen der Oberfläche, die Kommandozeilen-Werkzeuge (Crawler, Analyse-Skripte) und die Test-Suite.

---

## 1. Überblick

Das Tool besteht aus drei Bausteinen:

| Baustein | Zweck |
|---|---|
| **Streamlit-App** (`app.py`) | Interaktive Exploration: Import, Filter, Zeitfenster, Merkmale, Qualitätsprüfung, Export, ML |
| **mini_crawler.py** | Eigener Webcrawler, erzeugt das Datenformat für das Website-Modul (inkl. Screenshots, Asset-Index) |
| **Analyse-Skripte** (`check_*.py`) | Reproduzieren die Kennzahlen der beiden Papers (Korrelationen, Mixed Models, Sensor-Deltas, Webkomplexität) |

Die App behandelt drei getrennte Datenwelten in einer Oberfläche:

1. **Tabellarische Standarddaten** (CSV / Excel / JSON)
2. **Experiment-Trials**: Eventlogs (`events.ndjson`) + Sensorzeitreihen (`fusion_merged.ndjson`)
3. **Webcrawler-Daten**: pro Website Unterordner mit gecrawlten Seiten, Metadaten und Assets

---

## 2. Voraussetzungen & Installation

Benötigt: Python 3.12+, ca. 1 GB Speicher (inkl. Chromium für Screenshots).

```bash
# 1. Virtuelle Umgebung anlegen
python3 -m venv .venv
source .venv/bin/activate            # macOS/Linux

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Browser für Crawler-Screenshots (einmalig pro Maschine)
playwright install chromium
```

Ohne Schritt 3 funktioniert alles außer dem Screenshot-Export des Crawlers — der Crawler weist dann darauf hin und läuft ohne Screenshots weiter.

## 3. Anwendung starten

```bash
source .venv/bin/activate
streamlit run app.py
```

Die App öffnet sich im Browser (Standard: `http://localhost:8501`).

---

## 4. Datenformate

### 4.1 Experimentdaten (Trials)

Ein Hauptordner (z. B. `data/`) enthält pro Trial einen Unterordner:

```
data/
  T-1/
    events.ndjson          # Eventlog
    fusion_merged.ndjson   # Sensor-Zeitreihe
  T-2/
    ...
```

**`events.ndjson`** — eine JSON-Objekt-Zeile pro Event. Typische Zeilen:

```json
{"ts":1756049126078,"ts_iso":"2025-08-24T15:25:24.827Z","trialId":"T-1","type":"baseline:start"}
{"ts":1756049160105,"type":"task:start","domain":"gaming"}
{"ts":1756049260105,"type":"task:end","domain":"gaming"}
{"ts":1756049300000,"type":"tlx:submit","domain":"gaming","scores":{"frustration":35,"mentale":60}}
```

Wichtige Konventionen:

- **Timestamp-Schlüssel**: erkannt werden `ts`, `t`, `time`, `timestamp` sowie normalisierte Varianten wie `timestamp_ms`, `timestampMs`, `ts_ms`, `TimeMs`. Nicht benutzte Alias-Schlüssel werden aus den Event-Metadaten entfernt.
- **Event-Typen**: `task:start/end`, `baseline:start/end`, `questionnaire:start/end` werden klassifiziert; alles andere (z. B. `group:start`, `tlx:submit`, `trial:start`) bleibt Typ „unknown" und geht nur in die Eventdichte ein.
- **Domain**: optionales Feld `domain` pro Task-Event. Start/End-Paarung erfolgt **strikt pro Domain** (auch bei numerischen Werten wie `1`/`2`, die kanonisiert werden). Fehlt die Domain auf einer Seite, greift eine abgestufte Fallback-Regel.
- **Unsaubere Daten sind erwartet**: fehlende End-Events erzeugen unvollständige Segmente (kein Absturz), verwaiste End-Events werden als Qualitätsproblem gemeldet.

**`fusion_merged.ndjson`** — eine Zeile pro Abtastzeitpunkt, verschachtelte Sensordaten:

```json
{"ts":1756049121494,"rate_hz":10,
 "shimmer":{"GsrKOhm":5330.7,"GsrConductanceUS":0.187,"PpgmV":235.9,"AccX":7.66,...},
 "gaze":{"LeftX":0.581,"LeftY":0.572,"LeftPupilDiamMm":4.06,"LeftValidity":0,...}}
```

- Verschachtelte Objekte werden zu Kanalnamen mit Punkt-Notation (`shimmer.GsrKOhm`, `gaze.LeftX`).
- Nur numerische Blätter werden Kanäle; Uhrfelder (z. B. `gaze.SystemTimestampMs`, `shimmer.AppTimestampMs`) werden gefiltert — echte Signale mit ähnlichem Namen (z. B. `heart_timestamp`) bleiben erhalten.
- Fehlende Werte pro Zeile werden zu `None` gepolstert (Kanäle bleiben parallel zu den Timestamps).

### 4.2 Webcrawler-Daten (Websites)

Ein Hauptordner (z. B. `websites/`) enthält pro Website einen Unterordner:

```
websites/
  A_bpb/
    portal_meta.json        # Start-URL, Seitenzahl
    asset_index.json        # Asset-URL -> Typ, referenzierende Seiten, Shared-Flag
    shared_assets/          # Downloads der von >=2 Seiten genutzten Assets
    pages/
      1/  raw.html  screenshot.png  visible_text.json  links.json  forms.json  media.json  dom.json
      2/  ...
```

Diese Struktur wird vollständig automatisch von `mini_crawler.py` erzeugt (Abschnitt 9). Fehlende Dateien werden toleriert — der Loader markiert Verfügbarkeit, statt zu crashen.

### 4.3 Tabellarische Daten

CSV, XLSX und JSON über den Datei-Uploader in der Sidebar. JSON-Dateien erhalten zusätzlich eine Baumansicht.

---

## 5. Die Oberfläche — Tabs im Detail

### 5.1 Tabellarische Daten
Vorsicht mit Auswahl/Export (CSV/Excel/JSON/Markdown-Report), Sidebar-Filter (Textsuche, Wertebereiche, Kategorien), IQR-Ausreißeranalyse mit Detailansicht, Korrelations-Heatmap (optional mit Smart-Encode binärer Textspalten), Datenqualität (fehlende Werte gruppiert, Duplikate, konstante Spalten, Typenkonflikte).

### 5.2 Import
Pfade zu Trial-Hauptordner und Website-Hauptordner eingeben und laden. Bereits geladene IDs werden erkannt (keine Duplikate). Die Daten liegen im Session-State der laufenden Sitzung.

### 5.3 Dateninventar
Übersicht aller geladenen Quellen: Zeilen/Spalten der Tabellendaten (inkl. `DatasetRecord`-Details), Trials mit Event-/Kanal-/Sample-Zahlen, Websites mit Seiten-/Link-/Media-Zahlen.

### 5.4 Trials
Pro Trial vier Untertabs:
- **Timeline**: Segmente (Label, Domain, Typ, Dauer, Vollständigkeit) + Qualitätsprobleme, CSV-Export.
- **Events**: rohe, klassifizierte Eventliste.
- **Qualität**: Sensor-Checks mit einstellbarem Gap-Schwellenwert (s. Abschnitt 8), CSV-Export.
- **Analysen**: **Eventdichte** (Events/s je Segment; Grenzereignisse werden eindeutig zugewiesen — END zählt zum früheren, START zum späteren Segment) und **Baseline-vs-Task-Vergleich** (Kanal-Mittelwerte je Segmenttyp; Gruppierung nach Typ, nicht nach Label; wiederholte Segmente fließen alle ein).

### 5.5 Zeitfenster
Der Kern für Sensordaten (Details in Abschnitt 6): Stream-Auswahl (kompletter Fusion oder Einzelmodalität), optionale Synchronisation, drei Fenster-Modi, Merkmalsberechnung, Erkennung auffälliger Fenster, Export als lange und breite Feature-Tabelle.

### 5.6 Sensoranalyse
Modalitätsbezogene Übersicht über alle Trials: Qualitäts-Tabelle je Trial/Modalität (Samples, doppelte Timestamps, Max-Gap, Issues, OK-Flag) mit einstellbarem Gap-Schwellenwert sowie Kanalstatistik (gültige Samples, Fehlerrate, min/max/Mittelwert) — beide als CSV exportierbar.

### 5.7 Websites
Seiten-Übersicht mit Portal-Metadaten und Asset-Index (Shared-Assets-Inventar), aggregierte Merkmale (Mittelwert/Max/Summe über alle Seiten), Screenshot-Galerie verknüpft mit den Seitenmerkmalen, sowie **Konsistenzanalyse** (Screenshots ↔ JSON-Merkmale): leere/unlesbare Screenshots, Inhalt ohne Screenshot, raw.html/dom.json-Mismatches werden als Befund-Tabelle mit CSV-Export ausgewiesen.

### 5.8 Reporting
Zentrale Exporte: Timeline-/Qualitäts-CSV und Markdown-Report pro Trial; Pages-CSV/-Excel und Website-Report; Website-Übersicht aller geladenen Seiten.

### 5.9 ML
Arbeitet ausschließlich auf **aggregierten Merkmals-Tabellen** (exportierte Fenster-Features als CSV wieder hochladen oder beliebige Tabellendaten): K-Means (Silhouette/Inertia), Isolation Forest (Anomalien), Random-Forest-Klassifikation und -Regression mit Feature-Importances und Modellmetriken. Ergebnisse als CSV exportierbar.

---

## 6. Zeitfenster-Manager im Detail

### Modi
| Modus | Bedeutung | Parameter |
|---|---|---|
| `fixed` | Ein Fenster ab Stream-Beginne + Offsets | Fensterlänge, Offset Start/Ende |
| `sliding` | Gleitende Fenster über den ganzen Stream | Fensterlänge, Schrittweite |
| `task` | Ein Fenster pro Segment mit gewähltem Label (inkl. Domain, z. B. `task [gaming]`) | Task-Label, Offsets |

Ungültige Definitionen (leere Fenster, negative Dauer, Offset jenseits des Streams) werfen eine klare Fehlermeldung in der UI statt leerer Ergebnisse.

### Merkmale pro Kanal und Fenster
`mean, median, std, variance, min, max, range, peak_count, trend, n_samples, missing_rate` —
`missing_rate` ist die Fehlerrate (Anteil None/unparseabler Samples im Fenster); Kanäle ohne gültige Werte bleiben mit `missing_rate=1.0` sichtbar. Welche Kennzahlen in Tabelle und langem CSV-Export erscheinen, ist per Multiselect wählbar; leere Fenster (kein gültiges Sample) werden separat gezählt und gewarnt.

### Auffällige Fenster
Nach jeder Berechnung werden Fenster markiert, deren `mean`- oder `std`-z-Score (pro Kanal über alle Fenster) den Schwellenwert ±2 überschreitet oder die zu wenige Samples (<5) enthalten. Die Flags inkl. Grund stehen in der Tabelle und im CSV-Export.

### Definitionen versionierbar speichern (AP6)
- **Speichern**: Name vergeben → „Aktuelle Konfiguration speichern". Jede Speicherung erzeugt eine **neue Version** (Append-only, niemals Überschreiben).
- **Laden**: Eintrag auswählen → Werte werden vor der Widget-Erzeugung angewandt (kein Streamlit-Konflikt). Task-Labels werden gegen die aktuelle Trial validiert; unbekannte Labels werden zurückgesetzt (mit Hinweis), ein Trial-Wechsel setzt veraltete Auswahlen zurück.
- **Persistenz**: `window_definitions.json` im Arbeitsverzeichnis (git-ignoriert). Format:

```json
{"next_id": 3, "definitions": [
  {"id": 1, "name": "baseline_2s", "version": 1,
   "created_at": "2026-09-08T10:14:03", "params": {"mode": "sliding", "duration_ms": 2000.0, ...}}]}
```

### Synchronisation (AP7)
Optional vor der Fensterung einschalten:
- **Modalitäten trennen**: Fusion-Stream wird in `shimmer_physio` und `eye_tracking` zerlegt (Kanalpräfixe).
- **Resampling**: alle Streams/Modalitäten erhalten **ein gemeinsames, identisches Zeitraster** (`earliest` = frühester Start bis spätestes Ende, `latest` = Überschneidung).
- **Lücken-Ehrlichkeit**: Rasterpunkte, die weiter als 2 Rasterschritte vom nächsten echten Sample liegen, bleiben `None` — über Aufzeichnungslücken wird nicht interpoliert. Echte Messpunkte an Lückengrenzen bleiben immer erhalten.
- **Schutz**: `target_hz ≤ 0` und Raster > 5 Mio. Punkte (z. B. 24 h @ 1000 Hz) werfen klare Fehler statt Speicherproblemen.

---

## 7. Exporte

| Export | Ort | Format |
|---|---|---|
| Fenster-Features (lang, mit Flags / breit, 1 Zeile pro Fenster) | Zeitfenster-Tab | CSV |
| Timeline, Eventdichte, Baseline-vs-Task, Qualitätsreport | Trials-Tab | CSV |
| Pages / Website-Übersicht, Markdown-Reports | Reporting-Tab | CSV, XLSX, MD |
| Tabellarische Daten | Tabellarische-Daten-Tab | CSV, XLSX, JSON, MD |

---

## 8. Qualitätsprüfungen (AP8)

Pro Stream und Kanal werden geprüft:

- **Doppelte Timestamps** (global) und **Sampling-Lücken** (Schwellenwert einstellbar, Standard 3000 ms)
- **Fehlende Werte** pro Kanal (`None`-Rate)
- **Plausibilitätsbereiche** je Kanaltyp: Herzfrequenz 30–220, PPG 0–4096 mV, GSR 0–100 µS / 0.01–5 MΩ, Gaze-Koordinaten −0.2–1.2, Pupille 1–10 mm, Temperatur 20–45 °C, IMU (Acc/AccWr ±16 g, Gyro ±2000 °/s, Mag ±400 µT), EEG/OpenBCI ±4000 µV (Reservierung). Gaze-Matching erkennt die realen Kanalnamen (`LeftX/RightX/LeftY/RightY`).
- **Kanal-Ausfälle**: lange konstante Wertfolgen (≥ 5 % der Samples und ≥ 50 Samples) — binäre Validitätsflags ausgenommen; `None`-Lücken zählen nicht als Ausfall, sondern als fehlende Werte.

Bekannte Datenlage: T-10 besitzt kein vollständiges Baseline-Segment (dort ist der Baseline-vs-Task-Vergleich folglich leer — das ist korrekt, kein Bug).

---

## 9. Webcrawler: mini_crawler.py

```bash
python mini_crawler.py <start_url> <output_dir> [max_pages] [--no-screenshots] [--no-asset-download]
```

- Crawlt **nur gleiche Domain**, respektiert `robots.txt` (Disallow-Pfade), 1 s Delay zwischen Seiten, max. 25 Seiten (Standard).
- Pro Seite: `raw.html`, strukturierte JSONs (Links, Formulare, Medien, sichtbarer Text, DOM-Baum), **Screenshot** (Playwright/Chromium, 1280×800).
- Pro Website: `portal_meta.json`, `asset_index.json` (alle Asset-Referenzen mit Shared-Flag) und `shared_assets/` (Downloads geteilter Assets; Limit 20 Dateien / 5 MB je Datei).
- URL-Normalisierung für De-Duplizierung: Fragmente entfernt, Query-Parameter sortiert, leerer Pfad → `/`.

Beispiel:

```bash
python mini_crawler.py https://www.hs-rm.de/ websites/B_hsrm 15
```

**Screenshots nachziehen** (bestehende Crawls, ohne die JSONs zu verändern):

```bash
python backfill_screenshots.py websites
```

Die Loader erkennen alternativ benannte Dateien (`events.json`, `fusion_merged.json`, `Links.json`, `dom_v2.json`, `openbci_*.ndjson` …), kanonische Namen haben Vorrang.

---

## 10. Analyse-Skripte (Paper-Reproduktion)

Alle Skripte laufen direkt im Projektverzeichnis (`data/` muss vorhanden sein) und schreiben Ergebnisse nach stdout bzw. `figures/`:

| Skript | Zweck |
|---|---|
| `check_correlations.py` | Pearson-Korrelation Taskdauer × NASA-TLX (Frustration, mentale Last) + Scatter-Plots |
| `check_mixed_model.py` | Inferenzstatistik Paper 1 Abschnitt 4.3: personen-geclusterter Bootstrap, MixedLM (Random Intercept), innerhalb-Person-Zentrierung |
| `check_sensor_deltas.py` | Baseline-zentrierte Domänen-Deltas für Pupillendurchmesser und Hautleitwert (Paper 1 Abschnitt 4.4) |
| `check_web_analysis.py` | Alle Kennzahlen Paper 2 (Webkomplexität) aus `new_web_features.csv`: k-Scan, Feature-Importance (MDI + Permutation), CV, Bootstrap, Stabilität — mit fest dokumentierten Seeds |

Nicht reproduzierbar sind allein die HTTP-Antwortzeiten (Tabellen 7/8 in Paper 2) — die Messdaten wurden nicht archiviert; dies ist im Paper gekennzeichnet.

---

## 11. Tests ausführen

```bash
source .venv/bin/activate
pytest tests/            # komplette Suite
pytest tests/test_synchronization.py -v    # einzelne Datei
```

- Aktuell **143 Tests**, alle ohne lokale Projektdaten lauffähig (funktioniert auch in einem frischen `git clone`, da `data/` git-ignoriert ist).
- Der einzige Real-Data-Test überspringt sich selbst, wenn `data/` fehlt (`skipif`-Marker).
- Enthalten: Unit-Tests für Synchronisation/Segmentierung/Loader/Statistiken, Store-Roundtrips und **AppTest-Ende-zu-Ende-Tests** (Fensterdefinitionen speichern/laden, Trial-Wechsel, ML, Reporting).

---

## 12. Projektstruktur

```
app.py                  Streamlit-Einstieg (Tabs, Sidebar-Upload)
mini_crawler.py         Webcrawler (CLI)
backfill_screenshots.py Screenshot-Nachzug für bestehende Crawls
check_*.py              Paper-Reproduktions-Skripte
src/
  session.py            zentrale Session-Verwaltung
  loaders/              tabular / trial / website / sensor Loader (+ Sortierung)
  models/               Datenmodelle (DatasetRecord, TrialRecord, Segment,
                        WindowDefinition, PageRecord, WebsiteRecord, ...)
  preprocessing/        segmentation (Timeline), windowing (Fenster),
                        synchronization (Split + Resampling),
                        quality_checks (AP8), window_store (AP6-Persistenz)
  feature_engineering/  sensor_features (Fenster-Merkmale), web_features
  analysis/             statistics (Eventdichte, Baseline-vs-Task, auffällige
                        Fenster), reporting (Exporte/Reports), ml_analysis,
                        web_consistency (Screenshot-JSON-Konsistenz)
  ui/                   ein Modul je Tab (+ styles)
tests/                  pytest-Suite inkl. AppTest
data/                   Trial-Rohdaten (git-ignoriert)
websites/               gecrawlte Websites (versioniert)
figures/                erzeugte Abbildungen
```

---

## 13. Häufige Probleme (FAQ)

| Problem | Ursache / Lösung |
|---|---|
| „Keine Trial-Ordner gefunden" | Pfad muss der **Hauptordner** sein, der die T-x-Unterordner enthält (nicht der einzelne Trial). |
| Crawler erzeugt keine Screenshots | `playwright install chromium` ausführen (Abschnitt 2). |
| Baseline-vs-Task bei T-10 leer | T-10 hat kein vollständiges Baseline-Segment — Datenlage, kein Fehler. |
| „Resampling würde … Rasterpunkte erzeugen" | `target_hz` senken oder Zeitbereich einschränken (Speicherschutz, Abschnitt 6). |
| Geladene Daten nach Neustart weg | Session-State ist flüchtig; Ordner im Import-Tab erneut laden. `window_definitions.json` dagegen persistsiert. |
| Viele `None`-Werte nach Synchronisation | Echte Aufzeichnungslücken werden nicht interpoliert (Abschnitt 6 „Lücken-Ehrlichkeit"). |
| `streamlit: command not found` | Virtuelle Umgebung aktivieren oder `python -m streamlit run app.py` nutzen. |

---

## 14. Was nicht in der Versionskontrolle liegt

`.gitignore` schließt aus: `data/` (Trial-Rohdaten, ~215 MB), `window_definitions.json`, generierte Plots (`paper1_scatter_*.png`), Poster-Projekt (`poster_*`, `make_posters_pptx.py`, `c.tex`), `Projektplan_*.docx` sowie `.venv/`, `__pycache__/`, `.claude/`. Die gecrawlten `websites/` sind dagegen **versioniert** und in einem Clone vorhanden. Ein frischer Clone enthält Code + Tests + Website-Beispieldaten und ist ohne die lokalen Trial-Daten voll testfähig (Abschnitt 11).
