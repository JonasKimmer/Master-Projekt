# Kognitive Beanspruchung bei der Exploration interaktiver Datenvisualisierungen: Domäneneffekte und Belastungsindikatoren

**Jonas Kimmer**
**[BITTE VOR ABGABE ERGÄNZEN: Hochschule · Studiengang · Matrikelnummer · Betreuer:in · Abgabedatum]** · 2026

---

## Zusammenfassung

Bearbeitungszeit gilt in Usability-Studien häufig unkritisch als Proxy für kognitive Beanspruchung, obwohl unklar ist, ob sie tatsächlich mentale Last oder andere Faktoren wie Frustration und Domänenvertrautheit abbildet. Diese Studie untersucht anhand einer Sekundäranalyse eines multimodalen Datensatzes (N = 18), ob sich die kognitive Beanspruchung bei der Exploration interaktiver Datenvisualisierungen je nach Inhaltsdomäne unterscheidet, und ob Bearbeitungszeit ein verlässlicher Indikator für kognitive Last ist.

Die Teilnehmenden bearbeiteten je 15 Aufgaben über fünf Visualisierungstypen in drei Inhaltsdomänen (Gaming, Gesundheit, Stadtplanung). Der Aufwand wurde über NASA-TLX (Raw-Version) erfasst, ergänzend wurden Shimmer3-Sensoren und ein Tobii-Eye-Tracker eingesetzt. Die mentale Beanspruchung lag in allen Domänen auf nahezu identischem Niveau (M = 61,5–63,2), Frustration variierte deskriptiv zwischen den Domänen (Gaming M = 47,4, Stadt M = 36,8), folgte dabei aber nicht der subjektiven Domänenvertrautheit. Bearbeitungszeit korrelierte deutlich mit Frustration (r = 0,56), nicht mit mentaler Anforderung (r = 0,03); der Zusammenhang blieb nach Kontrolle für Personeneffekte bestehen (zentriert r = 0,52; Mixed-Model: Slope = 0,133, p < 0,0001). Bearbeitungszeit erweist sich damit als Indikator für Frustration, nicht für kognitive Last; die Wirkrichtung zwischen beiden bleibt offen. Alle Befunde sind angesichts von N = 18 Personen explorativ; das Mixed-Model ist der einzige formale Test der Studie.

**Schlüsselwörter:** Kognitive Last, NASA-TLX, Datenvisualisierung, Domäneneffekte, Bearbeitungszeit

---

## Abbildungsverzeichnis

- **Abbildung 1:** NASA-TLX-Dimensionen nach Domäne (Boxplots, Abschnitt 4.1)
- **Abbildung 2:** Kumulierte Bearbeitungszeit × Frustration / Mentale Anforderung (Abschnitt 4.3)

## Tabellenverzeichnis

- **Tabelle 1:** NASA-TLX-Scores nach Domäne (Abschnitt 4.1)
- **Tabelle 2:** Bearbeitungszeit nach Domäne (Abschnitt 4.2)
- **Tabelle 2b:** Bearbeitungszeit nach Aufgabenposition / Visualisierungstyp (Abschnitt 4.2)
- **Tabelle 3:** Pearson-Korrelationen Bearbeitungszeit × NASA-TLX (Abschnitt 4.3)
- **Tabelle 3b:** Absicherung gegen Pseudoreplikation: Zentrierung, Bootstrap, Mixed-Model (Abschnitt 4.3)
- **Tabelle 4:** Deskriptive Statistik ausgewählter Sensorkanäle (Abschnitt 4.4)
- **Tabelle 5:** Baseline-zentrierte Domänen-Deltas (Abschnitt 4.4)

---

## 1. Einleitung

### 1.1 Motivation und Problemstellung

Datenvisualisierungen sollen komplexe Sachverhalte einfacher zugänglich machen, doch mit zunehmender Komplexität der Darstellungen wächst die Gefahr kognitiver Überlastung (Sweller, 1988). Klassische Usability-Studien messen Fehlerrate und Bearbeitungszeit und setzen letztere häufig stillschweigend mit Beanspruchung gleich, zwei Personen können aber dieselbe Aufgabe gleich schnell lösen und dabei dennoch unterschiedliche kognitive Last erleben. Ob Bearbeitungszeit tatsächlich mentale Last abbildet oder eher Frustration und Domänenvertrautheit, bleibt damit offen.

Die verfügbaren Messwege haben dabei jeweils eigene Grenzen. Subjektive Befragungen wie der NASA-TLX erfassen nur retrospektive Einschätzungen. Physiologische Sensordaten könnten eine kontinuierliche Ergänzung darstellen, ihre Validität ist im Kontext der Datenvisualisierung jedoch kaum untersucht. Offen ist zudem die Rolle der Inhaltsdomäne selbst: Dieselbe Visualisierungsform kann je nach dargestellter Domäne unterschiedlich stark beanspruchen, etwa weil Fachvokabular, Zahlenformate oder die emotionale Relevanz der Inhalte variieren. Ob und wie stark sich dieser Domäneneffekt von der reinen Visualisierungskomplexität trennen lässt, ist bislang kaum systematisch untersucht worden.

### 1.2 Zielsetzung

Diese Studie prüft, ob sich kognitive Beanspruchung systematisch zwischen drei Inhaltsdomänen unterscheidet, und ob Bearbeitungszeit den subjektiv empfundenen Aufwand zuverlässig abbildet. Ausgewertet werden die Daten einer bestehenden Erhebung aus NASA-TLX-Fragebögen, physiologischen Sensordaten und Eye-Tracking mit einem eigens entwickelten Analyse-Tool.

> _Unterscheidet sich die kognitive Beanspruchung bei der Exploration interaktiver Datenvisualisierungen je nach Inhaltsdomäne, und ist Bearbeitungszeit ein verlässlicher Indikator für kognitive Last?_

Zwei Nebenfragestellungen schärfen sie: Welche Domäne erzeugt die höchste Frustration? Wie hängen Bearbeitungszeit und die einzelnen NASA-TLX-Dimensionen zusammen?

---

## 2. Stand der Technik

### 2.1 Kognitive Last und subjektive Messung

Die Cognitive-Load-Theorie (Sweller, 1988) beschreibt, wie die begrenzte Kapazität des Arbeitsgedächtnisses konventionelle Lösungsstrategien mit dem Aufbau von Schemata konkurrieren lässt; die heute gebräuchliche Unterscheidung in intrinsische, extrinsische und lernbezogene ("germane") Last wurde erst in der Weiterentwicklung der Theorie eingeführt (Paas et al., 2003). Für Datenvisualisierungen ist vor allem die extrinsische Last relevant: Ein unübersichtliches Dashboard zwingt Nutzende, mehr Ressourcen in die Entschlüsselung der Darstellung selbst zu investieren, statt sie für die inhaltliche Analyse aufzuwenden. Der NASA-TLX (Hart & Staveland, 1988) ist das meistgenutzte Instrument zur subjektiven Workload-Erfassung. In einer Retrospektive von 20 Jahren Nutzung dokumentiert Hart (2006), dass ein erheblicher Teil der Anwendungen die ungewichtete Roh-Version (Raw TLX) verwendet, die ohne die paarweisen Gewichtsvergleiche auskommt; die vorliegende Studie folgt dieser Konvention.

### 2.2 Evaluation in der Informationsvisualisierung

Wie in der Informationsvisualisierung evaluiert wird, ist selbst Gegenstand systematischer Bestandsaufnahmen: Isenberg et al. (2013) analysierten 581 Beiträge von zehn Jahren der IEEE-Visualization-Konferenz hinsichtlich ihrer Evaluationspraxis und zeigen, dass messbare Leistungskennzahlen, darunter vornehmlich Zeit und Genauigkeit, die dominierende Rolle spielen. Lam et al. (2012) strukturieren empirische Studien in sieben Szenarien und weisen ebenfalls aus, dass Benutzungszeit als Standardmetrik gilt. Damit wird Bearbeitungszeit routinemäßig als Belastungs- oder Leistungsindikator herangezogen, was die Frage aufwirft, was sie tatsächlich misst.

### 2.3 Physiologische Indikatoren

Drei physiologische Messverfahren gelten als etablierte kontinuierliche Indikatoren kognitiver Beanspruchung (Beatty, 1982; Dawson et al., 2007): Pupillometrie, Hautleitwert und Herzrate via Photoplethysmographie (PPG). Hautleitwert misst die elektrische Leitfähigkeit der Haut, die mit Erregung steigt; PPG misst Blutvolumenänderungen über Lichtabsorption. Erste Arbeiten übertragen Pupillometrie bereits in den Visualisierungskontext: Toker und Conati (2017) zeigen in einer Vorstudie, dass Pupillendilatation kognitive Workload beim Lösen von Diagrammaufgaben (Balkendiagramme) abbilden kann. Alle drei Verfahren erfordern jedoch eine gesonderte Validierung gegenüber NASA-TLX-Scores; zudem ist die Pupille nach Mathôt (2018) nur ein bedingt verlässlicher Indikator, solange mentale Anstrengung und allgemeine Erregung nicht getrennt werden können.

### 2.4 Domänenvertrautheit

Weniger klar ist die Befundlage zur Rolle der Domänenvertrautheit. Die Expertise-Forschung zu Diagrammlesekompetenz geht meist davon aus, dass Vorwissen die kognitive Last senkt, weil vertraute Strukturen schneller in bestehende Schemata eingeordnet werden können (Schema-Theorie, vgl. Paas et al., 2003). Empirische Arbeiten, die Vertrautheit und affektive Reaktionen wie Frustration getrennt erfassen, sind jedoch selten, meist dient nur die Bearbeitungsgeschwindigkeit als Erfolgsindikator.

---

## 3. Methodik

### 3.1 Versuchspersonen und Design

Die Daten stammen aus einer bestehenden Erhebung und wurden anonymisiert, mit Trial-IDs statt Personendaten, zur Analyse bereitgestellt. Für Einwilligung und Datenschutz der physiologischen Messungen ist die Ursprungserhebung verantwortlich, auf deren Unterlagen diese Arbeit keinen Zugriff hatte.

An der Studie nahmen N = 18 Personen teil, ein Convenience-Sample aus dem Hochschulkontext. Demografische Angaben liegen für 17 vor, überwiegend jung (18–24 Jahre, 13 von 17), ausgeglichen nach Geschlecht (9/8), die größte Gruppe (8 von 17) arbeitet im IT-Bereich. Die subjektive Domänenvertrautheit war für Stadtplanung am geringsten (M = 28,5), für Gaming am höchsten (M = 44,1, SD = 26,4), Gesundheit lag dazwischen (M = 40,4).

Das Design war vollständig within-subject mit fünf Visualisierungstypen in drei Domänen. Die Domänenreihenfolge wurde nach einem Lateinischen Quadrat annähernd balanciert (5–7 von 18 je Blockposition), die Reihenfolge der Visualisierungstypen (Timeline, Scatter, Combo, Heatmap, Dashboard) war für alle Teilnehmende identisch. Der Ablauf umfasste Kalibrierung, eine 30-sekündige Baseline, drei Domänenblöcke mit je fünf Aufgaben und anschließendem NASA-TLX, bei einer Gesamtdauer von 45 bis 60 Minuten.

### 3.2 Aufgaben und Visualisierungstypen

Die Teilnehmenden bearbeiteten Aufgaben aus drei Domänen (Gaming mit Spielerstatistiken, Gesundheit mit Patientendaten, Stadtplanung mit Infrastrukturdaten) über fünf Visualisierungstypen (Timeline, Scatter, Combo, Heatmap, Dashboard) in fester Reihenfolge.

Nach jedem Domänenblock wurde der NASA-TLX in der Raw-Version erhoben, also ohne paarweise Gewichtsvergleiche. Das Instrument liefert sechs Dimensionswerte zwischen 0 und 100 (mentale, körperliche und zeitliche Anforderung, Leistung, Anstrengung, Frustration), im Datensatz in 5er-Schritten. Alle Analysen betrachten die Dimensionen getrennt, ein Gesamtwert wird nicht gebildet, Scores auf Diagrammtyp-Ebene liegen nicht vor.

Zur Dimension „Leistung“ ist die Scoring-Richtung zu beachten: In der Original-Konvention bedeutet ein hoher Wert eine schlechtere Selbsteinschätzung, die von der Erhebungs-App implementierte Richtung ist nicht dokumentiert. Eine indirekte Prüfung über die Korrelation der Leistung-Dimension mit Frustration, Mentaler Anforderung und Anstrengung über alle 54 TLX-Datensätze liefert kein Datenindiz: Die Werte liegen nahe null in alle Richtungen (−0,09 / +0,03 / +0,04), während das Instrument bei anderen Dimensionspaaren klare Zusammenhänge zeigt (Frustration × Mentale Anforderung: +0,58). Die Konvention lässt sich aus den Daten also nicht ableiten und bleibt offen.

### 3.3 Messinstrumente und Datenvorverarbeitung

Eingesetzt wurden ein Shimmer3-Sensor am Handgelenk (Hautleitwert, Herzrate via PPG, Bewegungssensoren) und ein Tobii Eye-Tracker (Blickpunkt, beidseitiger Pupillendurchmesser mit Gültigkeitsflags). Die Daten liegen als fusionierter Stream auf einem 10-Hz-Raster vor, effektiv im Mittel 9,6 Hz (Shimmer) beziehungsweise 9,5 Hz (Tobii, native etwa 33 Hz), 83,5 % der Pupillen-Samples sind als gültig markiert.

Die Auswertung extrahiert aus den Eventlogs Start- und Endzeitstempel je Aufgabe, meist mit einem Baseline-Segment pro Trial, in drei Trials mit zweien. Die kumulierte Bearbeitungszeit je Domäne ist die Summe der fünf Aufgabendauern eines Blocks. Sampling-Lücken, doppelte Zeitstempel und Plausibilitätsverletzungen wurden automatisch geprüft, dabei fanden sich 120 negative Hautleitwert-Samples in fünf Trials (T-3, T-7, T-8, T-12, T-14), die als Rohwerte verbleiben.

Ein Datenartefakt erfordert zwei Paarungslogiken: In T-3/Stadt existiert ein verwaister `task:start` ohne End-Event (271 Starts stehen 270 Ends gegenüber, die Lücke zum nächsten Start beträgt rund 825 s). Die tabellarische Auswertung paart First-In-First-Out und weist die Lücke als eigene, rund 14 Minuten lange Aufgabe aus, daraus resultiert der Ausreißer in 4.2. Die Korrelationsauswertung behandelt einen neuen Start derselben Domäne als Neustart und verwirft den verwaisten Start. Mit der FIFO-Paarung reproduziert sich Tabelle 2 exakt (Reproduktion: `check_correlations.py`).

Alle weiteren Analysen reproduzieren sich über `check_mixed_model.py` und `check_sensor_deltas.py` (s. Verfügbarkeitsstatement).

---

## 4. Ergebnisse

### 4.1 NASA-TLX nach Domäne

**Tabelle 1: NASA-TLX-Scores nach Domäne (N = 18, Skala 0–100, Stichproben-SD)**

| Dimension               | Gaming M (SD) | Gesundheit M (SD) | Stadt M (SD) |
| ----------------------- | ------------- | ----------------- | ------------ |
| Mentale Anforderung     | 61,5 (26,2)   | 62,6 (24,2)       | 63,2 (22,6)  |
| Körperliche Anforderung | 27,8 (28,8)   | 22,5 (26,9)       | 22,4 (27,4)  |
| Zeitliche Anforderung   | 28,9 (29,2)   | 27,0 (33,5)       | 25,6 (30,7)  |
| Leistung                | 41,4 (25,0)   | 41,8 (19,1)       | 49,7 (23,9)  |
| Anstrengung             | 51,2 (27,9)   | 45,1 (22,7)       | 46,3 (27,5)  |
| Frustration             | 47,4 (39,4)   | 43,5 (38,7)       | 36,8 (34,0)  |

Die mentale Anforderung liegt in allen Domänen auf nahezu identischem Niveau. Die Differenz zwischen höchstem und niedrigstem Domänenmittel (Δ = 1,7; 63,2 in Stadt vs. 61,5 in Gaming) ist angesichts der Streuung (SD ≈ 22–26) klein und ohne Signifikanztest nicht von Rauschen zu unterscheiden. Frustration weist die stärkste domänenabhängige Variation auf (Gaming vs. Stadt: Δ = 10,6). Die übrigen Dimensionen zeigen ähnliche Muster über alle Domänen und werden nicht weiter differenziert.

**Abbildung 1: NASA-TLX-Dimensionen nach Domäne**

![Abbildung 1: NASA-TLX-Boxplot](figures/paper1_abb1_tlx_boxplot.png)

_Boxplots aller sechs NASA-TLX-Dimensionen je Domäne (N = 18). Median, Interquartilsabstand und Ausreißer. Die Boxplot-Mediane zeichnen dasselbe Bild wie die Mittelwerte in Tabelle 1. Die Abbildung wird von `check_correlations.py` erzeugt._

### 4.2 Bearbeitungszeit nach Domäne

**Tabelle 2: Bearbeitungszeit in Sekunden (269 Aufgaben; 1 Ausreißer ausgeschlossen; Stichproben-SD; Reproduktion: `check_correlations.py`)**

| Domäne     | N   | M (s) | SD (s) | Min | Max |
| ---------- | --- | ----- | ------ | --- | --- |
| Gaming     | 90  | 69,6  | 38,7   | 7   | 214 |
| Gesundheit | 90  | 75,2  | 54,4   | 7   | 310 |
| Stadt      | 89¹ | 68,7  | 32,5   | 16  | 164 |

¹ Ein Aufgabenmesswert (T-3, Stadt, 849 s) wurde als Datenerfassungsstörung ausgeschlossen (Ursache in 3.3).

Die mittlere Bearbeitungszeit liegt in allen drei Domänen in ähnlicher Größenordnung, Gesundheits-Aufgaben dauern am längsten und streuen zugleich am stärksten. Eine zweite Sichtweise ergibt sich aus der festen Reihenfolge der Aufgaben innerhalb eines Blocks: Weil jede Position einem Visualisierungstyp entspricht (3.2), weist Tabelle 2b die Bearbeitungszeit nach Aufgabenposition aus.

### 4.3 Korrelation zwischen Bearbeitungszeit und NASA-TLX

Tabelle 3 stellt die Pearson-Korrelationen zwischen kumulierter Bearbeitungszeit pro Domäne und den NASA-TLX-Dimensionen dar. Wegen Pseudoreplikation (53 Durchläufe von 18 Personen) werden die Werte explorativ gelesen, Inferenz liefern erst die Korrekturverfahren in Tabelle 3b. Nach Cohen (1988) entspricht r ≈ 0,5 einem großen Effekt.

**Tabelle 3: Pearson-Korrelationen Bearbeitungszeit × NASA-TLX**
_(N = 53 statt 54: Ausgeschlossen wurde T-4/Gesundheit mit 891 s kumulierter Dauer nach der >3-SD-Regel.)_

| Domäne     | r (Frustration) | r (Mentale Anf.) | r (Anstrengung) |
| ---------- | --------------- | ---------------- | --------------- |
| Gaming     | **0,56**        | 0,16             | 0,08            |
| Gesundheit | **0,61**        | 0,13             | 0,13            |
| Stadt      | **0,48**        | −0,26            | 0,08            |
| **Gesamt** | **0,56**        | 0,03             | 0,09            |

Die Zeile "Gesamt" poolt über alle Domänen und ist selbst pseudorepliziert; die Zeilenwerte beruhen auf je 17–18 Durchläufen.

**Abbildung 2: Bearbeitungszeit × NASA-TLX (Frustration und Mentale Anforderung)**

![Abbildung 2: Streudiagramm Bearbeitungszeit x TLX](figures/paper1_abb2_scatter_duration_tlx.png)

_Kumulierte Bearbeitungszeit pro Domänendurchlauf gegen Frustration (links) und mentale Anforderung (rechts), farblich nach Domäne, mit Regressionsgeraden je Domäne und gesamt (N = 53, ein Ausreißer ausgeschlossen). Die Abbildung wird von `check_correlations.py` erzeugt._

In Abbildung 2 steigen die drei domänenspezifischen Regressionsgeraden für Frustration übereinstimmend mit der Bearbeitungszeit an, wenn auch mit unterschiedlicher Steigung. Die Geraden zur mentalen Anforderung verlaufen dagegen uneinheitlich in unterschiedliche Richtungen.

Zur Absicherung gegen Pseudoreplikation folgen in Tabelle 3b Personen-Zentrierung, ein personen-geclusterter Bootstrap (5.000 Resamples) und ein Mixed-Model mit Random Intercept je Person (Reproduktion: `check_mixed_model.py`):

**Tabelle 3b: Absicherung gegen Pseudoreplikation (Zentrierung, Bootstrap, Mixed-Model)**

| Dimension           | r (unkorrigiert) | 95 %-CI (Fisher-z) | r (zentriert) | 95 %-CI (Bootstrap) | Mixed-Model Slope [95 %-CI] | p            |
| ------------------- | ---------------- | ------------------ | ------------- | ------------------- | --------------------------- | ------------ |
| Frustration         | 0,56             | [0,34, 0,72]       | **0,52**      | **[0,36, 0,70]**    | 0,133 [0,074, 0,192]        | **< 0,0001** |
| Mentale Anforderung | 0,03             | [−0,24, 0,30]      | 0,15          | [−0,11, 0,42]       | 0,013 [−0,032, 0,058]       | 0,574        |
| Anstrengung         | 0,09             | [−0,18, 0,35]      | −0,00         | [−0,38, 0,39]       | 0,001 [−0,041, 0,044]       | 0,945        |

Der Frustrations-Effekt bleibt nach Zentrierung nahezu unverändert und ist im Mixed-Model signifikant. Für mentale Anforderung und Anstrengung zeigt sich in keinem der drei Verfahren ein Effekt.

### 4.4 Sensordaten: Baseline-zentrierte Domänen-Deltas

Physiologische Sensordaten liegen für alle 18 Trials vollständig vor. Tabelle 4 zeigt die deskriptive Gesamtstatistik ausgewählter Kanäle über alle gültigen Samples ohne weitere Filterung.

**Tabelle 4: Deskriptive Statistik ausgewählter Sensorkanäle** _(alle gültigen (nicht-leeren) Samples aller 18 Trials, ohne weitere Filterung; Reproduktion: `check_sensor_deltas.py`)_

| Kanal                      | Einheit | M     | SD   | Min   | Max   |
| -------------------------- | ------- | ----- | ---- | ----- | ----- |
| Pupillendurchmesser links  | mm      | 4,56  | 0,81 | 1,51  | 7,17  |
| Pupillendurchmesser rechts | mm      | 4,59  | 0,85 | 1,39  | 7,73  |
| Hautleitwert (GSR)         | µS      | 2,46  | 4,63 | −1,00 | 24,77 |
| PPG-Rohsignal              | mV      | 182,9 | 34,6 | 59,3  | 244,7 |

**Tabelle 5: Baseline-zentrierte Domänen-Deltas (M (SD) über n = 17 Trials)**

| Kanal                    | Gaming       | Gesundheit   | Stadt        |
| ------------------------ | ------------ | ------------ | ------------ |
| Pupillendurchmesser (mm) | −0,07 (0,25) | −0,08 (0,31) | −0,02 (0,25) |
| Hautleitwert (µS)        | +1,64 (3,01) | +1,75 (3,17) | +1,31 (1,92) |

Der Pupillendurchmesser unterscheidet sich in keiner Domäne nennenswert von der Baseline (Deltas ≤ 0,08 mm bei Trial-SDs von 0,25–0,31). Der Hautleitwert steigt unter Aufgabe generell an (+1,3 bis +1,8 µS), die Domänen-Deltas überlappen jedoch vollständig. Ein domänenspezifisches Muster zeigen die Sensordaten damit nicht.

---

## 5. Diskussion

### 5.1 Domänenmuster: stabile mentale Last, domänenspezifische Frustration

Die mentale Anforderung bleibt über alle Domänen praktisch konstant (Δ = 1,7). Das widerspricht der Schema-Theorie aus Kapitel 2, wonach Vorwissen die Verarbeitung entlasten sollte. Stattdessen deutet vieles darauf, dass die Visualisierungsform die mentale Last stärker treibt als der dargestellte Inhalt. Kausal belegen lässt sich das nicht, weil Position und Typ konfundiert sind. Für die Gestaltungspraxis heißt das: Fachkompetenz allein reduziert die Beanspruchung nicht, die extrinsische Last muss über das Design minimiert werden.

Frustration verhält sich anders. Gaming erzeugt die höchste Frustration trotz höchster Vertrautheit, Stadt die niedrigste bei geringster Vertrautheit. Hohe Vertrautheit schützt also nicht vor Frustration. Dafür kommen drei Erklärungen in Betracht, die die Daten nicht trennen können: unterschiedliche Aufgabenschwierigkeit, emotional andere Besetztheit der Inhalte sowie frustrationstreibende Eigenschaften gerade der Gaming-Darstellungen. Frustration und mentale Anforderung sind damit empirisch trennbare Konstrukte und sollten nicht synonym als „kognitive Last“ behandelt werden.

Das physiologische Nullergebnis aus 4.4 kontrastiert mit Befunden wie denen von Toker und Conati (2017), die Pupillendilatation als Workload-Indikator bei Diagrammaufgaben validierten. Ein naheliegender Grund ist die Aggregation: Domänen-Blockmittel glätten kurzfristige Belastungsspitzen. Hinzu kommen fehlende Kontrollen für Beleuchtung und Bewegungsartefakte, beides bekannte Störgrößen (Dawson et al., 2007; Mathôt, 2018). Der gleichförmige Hautleitwert-Anstieg (+1,3 bis +1,8 µS in allen Domänen) ist mit einem allgemeinen Erregungsanstieg vereinbar, ohne Kontrollbedingung aber nicht interpretierbar.

### 5.2 Bearbeitungszeit als partieller Belastungsindikator

Bearbeitungszeit ist kein allgemeiner Proxy für kognitive Beanspruchung: Sie korreliert mit Frustration, nicht mit mentaler Anforderung oder Anstrengung. Die Korrelation legt zudem keine Wirkrichtung fest. Ebenso plausibel wie "Dauer erzeugt Frustration" ist die umgekehrte Lesart, dass Frustration zu Herumprobieren und damit längerer Dauer führt, etwa weil Aufgaben schwer verständlich sind. Das Querschnittsdesign kann nicht zwischen beiden unterscheiden; dafür wären zeitlich aufgelöste Messungen nötig, etwa Verhaltensmarker wie wiederholtes Zurückspringen zwischen Diagrammelementen statt einer retrospektiven Einzelbewertung am Blockende.

Studien, die Bearbeitungszeit als kognitive Last interpretieren, und das ist laut der Evaluationspraxis von Isenberg et al. (2013) eher die Regel, messen vermutlich primär aufgabenspezifische Schwierigkeit und affektive Reaktion. In der Praxis sollte eine lange Bearbeitungsdauer darum weniger als Hinweis auf hohe mentale Beanspruchung gelesen werden, sondern als Signal für eine mögliche Frustrationsquelle im Interface.

### 5.3 Einschränkungen

**Stichprobengröße und Pseudoreplikation:** N = 18 Personen ist die begrenzende Größe, alle Konfidenzintervalle sind entsprechend breit. Abgesehen vom Mixed-Model wurden keine formalen Signifikanztests durchgeführt, insbesondere der Frustrations-Unterschied zwischen Domänen blieb ungeprüft. Eine Absicherung von Effekten dieser Stärke erforderte etwa die doppelte Anzahl unabhängiger Personen (Fisher-z-Schätzung). Diese Schätzung beruht auf der Fisher-z-Transformation, einem Standardverfahren zur Stichprobengrößenplanung bei Korrelationen.

**Visualisierungsreihenfolge:** Die feste Reihenfolge der Visualisierungstypen erlaubt keine von Lerneffekten getrennte Aussage über deren relative Anforderung. Da NASA-TLX nur pro Domänenblock erhoben wurde, sind Visualisierungstyp-Effekte generell nicht prüfbar.

**Ausreißermanagement:** Die berichteten Korrelationen hängen vom Ausschlussentscheid ab (Robustheitsvermerk in Tabelle 3): Der Frustrations-Zusammenhang schwankt zwischen r = 0,43 und r = 0,56, je nachdem, welcher Ausreißer entfernt wird. Das Kriterium (>3 SD auf den Dauern) wurde nachträglich auf die Daten angewandt, nicht vorab festgelegt.

**Fehlende Sensor-TLX-Korrelation und Sensordatenqualität:** Die Sensordaten wurden nur baseline-korrigiert pro Domäne verglichen, nicht mit TLX-Scores korreliert. Gültigkeitsflags und Bewegungsartefakte gingen nicht in die Bereinigung ein, die 120 negativen Hautleitwert-Samples verblieben unkorrigiert. Gemessen an den Publikationsstandards für elektrodermale Messungen (Boucsein et al., 2012) erfüllt die Sekundärdatenanalyse deren Dokumentationsanforderungen nicht, und die effektive Pupillenrate von 9,5 Hz reduziert die zeitliche Auflösung.

**Kein objektiver Aufgabenerfolg:** Ob Aufgaben korrekt gelöst wurden, wurde nicht aufgezeichnet, die Event-Logs enthalten keine Korrekt-/Falsch-Information. Die naheliegende Konfundierung "schwierige Aufgabe → längere Dauer und höhere Frustration" ist damit nicht kontrollierbar; die TLX-Dimension "Leistung" (Selbsteinschätzung) ist die einzige verfügbare Performanz-Indikation. Künftige Erhebungen sollten den Aufgabenerfolg protokollieren.

**Erhebungsformat:** Die Domänenvertrautheit wurde nur über Selbsteinschätzung erfasst (Verzerrungsrisiko, z. B. Dunning-Kruger-Effekt), und der NASA-TLX wurde erst am Ende jedes Domänenblocks erhoben, sodass kurzfristige Belastungsspitzen im Blockmittel untergehen können.

---

## 6. Fazit

Die Ausgangsfrage war zweigeteilt, und die Antworten fallen unterschiedlich sicher aus. Zur ersten Teilfrage: Mentale Anforderung unterscheidet sich zwischen den Domänen nicht (Δ = 1,7 bei SD ≈ 22–26, ohne Inferenztest), Frustration deskriptiv schon (Δ = 10,6). Ein Domäneneffekt existiert also höchstens in der affektiven, nicht in der kognitiven Komponente, und auch das bleibt angesichts von N = 18 vorläufig. Zur zweiten Teilfrage, die mit Korrekturverfahren formal abgesichert wurde: Bearbeitungszeit ist ein Indikator für Frustration (zentriert r = 0,52, Mixed-Model p < 0,0001), nicht für mentale Anforderung. Wer nur Bearbeitungszeit oder einen globalen TLX-Gesamtwert erhebt, verdeckt genau diese Trennung; da Zeit messbare Standardmetrik der Visualisierungsevaluation ist (Isenberg et al., 2013; Lam et al., 2012), betrifft das einen breiten methodischen Konsens.

Für die Forschung folgt ein doppelter Bedarf: eine Replikation mit größerer, unabhängiger Stichprobe sowie zeitlich aufgelöste Messverfahren, die die offene Kausalrichtung zwischen Frustration und Dauer prüfen können. Die physiologischen Daten dieser Studie bleiben dafür eine auswertbare Grundlage, wurden hier aber nur deskriptiv genutzt.

Über den Datensatz hinaus wiederverwendbar ist auch der methodische Rahmen: Der alias-tolerante Ereignis-Loader, die beiden explizit dokumentierten Event-Paarungsverträge und die seed-festen Reproduktionsskripte sind kein Spezifikum dieser Erhebung, sondern ein übertragbares Muster für Sekundäranalysen vergleichbarer multimodaler Studien, einschließlich der durchgängig eingehaltenen Trennung von berichteten und reproduzierbaren Kennzahlen.

---

## Daten- und Analyse-Verfügbarkeit

Die Rohdaten sind aus Datenschutzgründen (physiologische Messungen, Einwilligung durch die Ursprungserhebung) nicht öffentlich. Alle Kennzahlen und beide Abbildungen sind über die im Projekt versionskontrollierten Skripte reproduzierbar: `check_correlations.py` (Korrelationen, Abbildungen 1 und 2, Tabellen 2 und 2b, Positionsdauern, Vertrautheitsmittel, DomainOrder-Balance, Start-/End-Zählungen), `check_mixed_model.py` (Tabelle 3b: Zentrierung, Bootstrap, Mixed-Model) und `check_sensor_deltas.py` (Tabelle 4 und 5, Messraten, Pupillen-Validität, negative Hautleitwert-Samples). Die Skripte nutzen denselben Lade- und Segmentierungsvertrag wie die Analyseumgebung; zentrale Verarbeitungsschritte sind durch eine automatisierte Testsuite abgesichert.

---

## Literatur

Beatty, J. (1982). Task-evoked pupillary responses, processing load, and the structure of processing resources. _Psychological Bulletin, 91_(2), 276–292.

Boucsein, W., Fowles, D. C., Grimnes, S., Ben-Shakhar, G., Roth, W. T., Dawson, M. E., & Filion, D. L. (2012). Publication recommendations for electrodermal measurements. _Psychophysiology, 49_(8), 1017–1034.

Cohen, J. (1988). _Statistical Power Analysis for the Behavioral Sciences_ (2nd ed.). Lawrence Erlbaum Associates.

Dawson, M. E., Schell, A. M., & Filion, D. L. (2007). The electrodermal system. In _Handbook of psychophysiology_ (3rd ed., pp. 159–181). Cambridge University Press.

Hart, S. G. (2006). NASA-Task Load Index (NASA-TLX); 20 years later. _Proceedings of the Human Factors and Ergonomics Society Annual Meeting, 50_(9), 904–908.

Hart, S. G., & Staveland, L. E. (1988). Development of NASA-TLX. _Advances in Psychology, 52_, 139–183.

Isenberg, T., Isenberg, P., Chen, J., Sedlmair, M., & Möller, T. (2013). A systematic review on the practice of evaluating visualization. _IEEE Transactions on Visualization and Computer Graphics, 19_(12), 2818–2827.

Lam, H., Bertini, E., Isenberg, P., Plaisant, C., & Carpendale, S. (2012). Empirical studies in information visualization: Seven scenarios. _IEEE Transactions on Visualization and Computer Graphics, 18_(9), 1520–1536.

Mathôt, S. (2018). Pupillometry: Psychology, physiology, and function. _Journal of Cognition, 1_(1), Artikel 16.

Paas, F., Renkl, A., & Sweller, J. (2003). Cognitive load theory and instructional design. _Educational Psychologist, 38_(1), 1–4.

Sweller, J. (1988). Cognitive load during problem solving. _Cognitive Science, 12_(2), 257–285.

Toker, D., & Conati, C. (2017). Leveraging pupil dilation measures for understanding visualization usage. _Proceedings of the ACM Symposium on Eye Tracking Research & Applications (ETRA '17), HAAPIE Workshop_.

---

## Ehrenwörtliche Erklärung

Hiermit erkläre ich ehrenwörtlich, dass ich die vorliegende Arbeit selbstständig und nur unter Verwendung der angegebenen Hilfsmittel angefertigt habe. Die aus fremden Quellen direkt oder indirekt übernommenen Gedanken sind als solche kenntlich gemacht. Die Arbeit wurde bisher in gleicher oder ähnlicher Form keiner anderen Prüfungsbehörde vorgelegt und ist noch nicht veröffentlicht.

Die Analyse- und Reproduktionsskripte wurden unter Zuhilfenahme eines KI-gestützten Programmierwerkzeugs (Claude Code) erstellt und geprüft. Die inhaltliche Konzeption, die Datenauswertung und die Interpretation liegen bei mir. Die Arbeit wurde gemäß den Regeln guter wissenschaftlicher Praxis erstellt.

**[ORT], den [DATUM]**

**[UNTERSCHRIFT]**

_(Unterschrift bei Abgabe in Dokument/PDF einfügen, diese Seite gehört zur Hausarbeit)_
