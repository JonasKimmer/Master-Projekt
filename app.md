# Projektplan: Erweiterung des Data-Discovery-Tools

> Modulare Erweiterung für Webcrawler-Daten, Eventlogs und multimodale Sensordaten

---

## Zielsetzung

Das bestehende Streamlit-basierte Data-Discovery-Tool soll so erweitert werden, dass neben tabellarischen Standarddaten auch zwei zusätzliche Datenwelten innerhalb derselben Oberfläche verarbeitet werden können:

1. Webcrawler- und Webarchivdaten
2. Multimodale Experimentdaten mit Eventlogs, Task-Strukturen und Sensorzeitreihen
3. Jeweils ein 10-seitiges Paper mit Forschungsfrage, Related Work und Beantwortung der Forschungsfrage

---

## Ordnerstruktur

### Experimentdaten

```
trials/
  t-1/
    events.ndjson
    fusion_merged.ndjson
  t-2/
    events.ndjson
    fusion_merged.ndjson
```

- **events.ndjson**: Log mit Timestamp wann bestimmte Events im Trial entstanden (z.B. nächste Task gestartet, Fragebogen gestartet etc.). Daten sind nicht sauber – es gibt nicht immer ein End-Event.
- **fusion_merged.ndjson**: Fortlaufendes JSON-Array mit JSON-Objekten. Enthält verschiedene Sensordaten mit Timestamp – Gemisch aus Eye-Tracking-Daten und physiologischen Daten (Herzrate etc.)

### Webcrawler-Daten

```
websites/
  1/
    pages/
      1/
        raw.html
        screenshot.png
        visible_text.json
        media.json
        links.json
        forms.json
        dom.json
      2/
        raw_html.json
        screenshot.png
        visible_text.json
        media.json
        links.json
        forms.json
        dom.json
    shared_assets/
    portal_meta.json
    asset_index.json
```

Der Website-Ordner ist die übergeordnete Einheit. Darin liegen Metadaten auf Website-Ebene, ein gemeinsamer Ordner für geteilte Assets sowie ein `pages/`-Unterordner mit nummerierten Unterordnern für einzelne gecrawlte Subpages.

---

## Ziel-Projektstruktur

```
project/
  app.py
  requirements.txt
  src/
    loaders/
      tabular_loader.py
      trial_loader.py
      website_loader.py
      sensor_loader.py
    models/
      records.py
      web_records.py
      experiment_records.py
    preprocessing/
      segmentation.py
      windowing.py
      synchronization.py
      quality_checks.py
    analysis/
      statistics.py
      reporting.py
    feature_engineering/
      sensor_features.py
      web_features.py
    ui/
      import_tab.py
      inventory_tab.py
      website_tab.py
      trials_tab.py
      windows_tab.py
      reporting_tab.py
      ml_tab.py
```

---

## Arbeitspakete

### AP1 – Bestehende App modularisieren

- `app.py` in klar getrennte UI- und Logikmodule zerlegen, ohne bestehenden Funktionsumfang zu verlieren
- Bestehende Bereiche (Import, Filter, Export, Korrelation, Ausreißeranalyse, Datenqualität) in wiederverwendbare Komponenten auslagern
- Zentrale Datenverwaltung einführen für konsistente Anbindung neuer Datenquellen

### AP3 – Gemeinsames internes Datenmodell

- Generische Python-Modelle definieren: `DatasetRecord`, `TrialRecord`, `WebsiteRecord`, `PageRecord`, `EventRecord`, `SensorStreamRecord`, `WindowDefinition`, `WindowFeatureRecord`
- Keine harte Bindung an Dateinamen – Datentypen und Beziehungen modellieren
- Zusätzliche Sensorquellen (z.B. OpenBCI) so modellieren, dass neue Kanäle ohne Umbau ergänzt werden können _(nur Modularität andenken, nicht vollständig umsetzen)_

### AP4 – Flexible Importschicht für Trials und Websites

- Importer für Trial-Hauptordner und Website-Hauptordner implementieren
- Automatische Erkennung der vorhandenen Unterordner und Dateien

### AP5 – Task- und Segmentlogik für Experimente

- `events.ndjson` pro Trial einlesen und in standardisierte Eventstruktur überführen
- Task-Start, Task-Ende, Baseline-Phasen und weitere experimentelle Ereignisse erkennen
- Trial-Timeline erzeugen für Visualisierung, Qualitätsprüfung und Fensterbildung

### AP6 – Zeitfenster-Manager (Feature-Windows)

- Konfiguration für feste, gleitende und task-basierte Zeitfenster
- Fensterlänge, Schrittweite, Bezugsbereich und Aggregationskennzahlen auswählbar
- Fensterdefinitionen versionierbar speichern für Reproduzierbarkeit

### AP7 – Sensorfusion und zeitliche Verdichtung

- `fusion_merged.ndjson` und künftige Sensorquellen in einheitliches Zeitreihenformat überführen
- Zeitstempel synchronisieren und pro Fensterlogik aggregieren
- Pro Fenster Merkmale berechnen: Mittelwert, Median, Std, Min/Max, Peak-Anzahl, Varianz, Fehlerrate, Trend

### AP8 – Qualitätsprüfungen für multimodale Daten

- Erkennen: Sampling-Lücken, doppelte Timestamps, Kanal-Ausfälle, leere Fenster, inkonsistente Zeitbereiche
- Kanalbezogene Plausibilitätschecks für Eye-Tracking, Herzfrequenz/PPG, GSR, IMU, EEG/OpenBCI _(z.B. keine negativen Herzfrequenzwerte)_
- Qualitätsberichte pro Trial exportierbar

### AP9 – Webcrawler-Modul integrieren

- Website-Hauptordner einlesen: Metadaten, Shared Assets, alle Page-Unterordner inventarisieren
- JSON-Dateien auf Seitenebene zu einheitlichem Seitenobjekt zusammenführen
- Screenshots in Vorschau anzeigen und mit strukturierten Seitenmerkmalen verknüpfen

### AP10 – Analysen für Webdaten

- Merkmale berechnen: Anzahl Links, Formulare, Medienelemente, DOM-Größe, Textmenge, strukturelle Tiefe
- Website-übergreifende Vergleiche zu Seitentypen, Komplexität und Inhaltsstruktur
- Aggregierte Merkmale auf Website-Ebene (Mittelwerte, Maximalwerte über alle Subpages)

### AP11 – Neue Tabs in der Oberfläche

- Tabs implementieren: Import, Dateninventar, Trials, Zeitfenster, Sensoranalyse, Website-Analyse, Reporting
- Standarddaten / Trial-Daten / Website-Daten klar getrennt halten

### AP12 – Export- und Reporting-Funktionen

- Fensterbasierte Feature-Tabellen exportieren
- Task- und Trial-Zusammenfassungen exportieren
- Website- und Page-Zusammenfassungen exportieren
- Automatische Markdown- oder Word-Berichte für Qualitätsprüfungen und Analyseergebnisse

### AP13 – Optionales ML-Modul _(niedrige Priorität)_

- ML nur auf aggregierten Fenster- oder Seitenmerkmalen, nicht auf Rohzeitreihen
- Klassifikation, Regression, Clustering oder Anomalieerkennung als Zusatzbereich
- Feature-Importances, Modellmetriken, Export der Merkmalsmatrizen
- **Empfehlung: Schnittstellen sauber definieren, vollständige Implementierung zurückstellen**

---

## Analysen – Trial- und Sensordaten

- Taskdauer, Eventdichte, Baseline-vs.-Task-Vergleiche pro Trial
- Vergleich von Eye-Tracking-, Herzfrequenz-, GSR-, IMU- und EEG-Merkmalen über Zeitfenster
- Identifikation auffälliger Fenster (erhöhte Aktivierung, starke Variabilität, schlechte Datenqualität)
- Verdichtete Exporttabellen pro Trial, pro Task oder pro Zeitfenster

## Analysen – Webcrawler-Daten

- Vergleich der strukturellen Komplexität einzelner Subpages innerhalb einer Website
- Vergleich verschiedener Websites: Textmenge, Linkdichte, Formularlast, DOM-Merkmale
- Konsistenzanalyse über Screenshots und strukturierte JSON-Merkmale
- Website-weite Übersichten: Assets, Seitenanzahl, Medientypen, Inhaltsverteilung
