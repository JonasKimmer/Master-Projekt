# Kognitive Beanspruchung bei der Exploration interaktiver Datenvisualisierungen: Domäneneffekte und Belastungsindikatoren

**Jonas Kimmer**  
Hochschule / Universität · Masterstudiengang · 2025

---

## Zusammenfassung

Bearbeitungszeit gilt in Usability-Studien häufig als Proxy für kognitive Beanspruchung, obwohl unklar ist, ob sie tatsächlich mentale Last oder andere Faktoren wie Frustration und Domänenvertrautheit abbildet. Diese Studie untersucht daher, ob sich die kognitive Beanspruchung bei der Exploration interaktiver Datenvisualisierungen je nach Inhaltsdomäne unterscheidet, und ob Bearbeitungszeit ein verlässlicher Indikator für kognitive Last ist. Achtzehn Versuchspersonen bearbeiteten je 15 Aufgaben über fünf Visualisierungstypen in drei Inhaltsdomänen (Gaming, Gesundheit, Stadtplanung). Der Aufwand wurde über NASA-TLX erfasst, ergänzend wurden Shimmer3-Sensoren und ein Tobii-Eye-Tracker eingesetzt. Die mentale Beanspruchung lag in allen Domänen konstant hoch (M = 62,4, SD = 23,6). Frustration variierte deskriptiv zwischen den Domänen (Gaming M = 47,4, Stadtplanung M = 36,8), folgte dabei aber nicht der subjektiven Domänenvertrautheit. Gaming wies zugleich die höchste Selbsteinschätzung (M = 44,1) und die höchste Frustration auf. Bearbeitungszeit korrelierte deutlich mit Frustration (r = 0,56), nicht mit mentaler Anforderung (r = 0,03). Der Zusammenhang blieb auch nach Kontrolle für Personeneffekte bestehen (Zentrierung und ein vollständiges Mixed-Effects-Modell, im Folgenden Mixed-Model genannt; r = 0,52 bzw. Slope = 0,133, p < 0,0001). Bearbeitungszeit erweist sich damit als Indikator für Frustration, nicht für kognitive Last. Die Wirkrichtung zwischen beiden bleibt offen. Die einfachen Domänen-Korrelationen selbst wurden ohne Signifikanztest berichtet, da sie durch Pseudoreplikation verzerrt sind. Das Mixed-Model ist der einzige formale Test dieser Studie und wird entsprechend vorsichtig interpretiert. Alle Befunde bleiben angesichts von N = 18 Personen explorativ.

**Schlüsselwörter:** Kognitive Last, NASA-TLX, Datenvisualisierung, Domäneneffekte, Bearbeitungszeit

---

## 1. Einleitung

### 1.1 Motivation und Problemstellung

Datenvisualisierungen sind in vielen Berufsfeldern unverzichtbar. Ihr impliziter Anspruch ist es, komplexe Sachverhalte einfacher zugänglich zu machen. Mit zunehmender Datenmenge und Komplexität der Visualisierungsformen steigt jedoch die Gefahr kognitiver Überlastung (Sweller, 1988). Klassische Usability-Studien messen Fehlerrate und Bearbeitungszeit, erfassen aber nicht, wie stark das Arbeitsgedächtnis dabei beansprucht wird, denn zwei Personen können dieselbe Aufgabe gleich schnell lösen und dabei dennoch unterschiedliche kognitive Last erleben.

Bearbeitungszeit gilt häufig als Proxy für kognitive Beanspruchung, obwohl unklar ist, ob sie tatsächlich mentale Last oder andere Faktoren wie Frustration und Domänenvertrautheit abbildet. Subjektive Befragungen wie der NASA-TLX erfassen nur retrospektive Einschätzungen. Physiologische Sensordaten könnten eine kontinuierliche Ergänzung darstellen, wobei ihre Validität im Kontext der Datenvisualisierung bislang kaum untersucht ist.

Ein weiterer offener Punkt betrifft die Rolle der Inhaltsdomäne selbst: Dieselbe Visualisierungsform kann je nach dargestellter Domäne unterschiedlich stark beanspruchen, etwa weil Fachvokabular, Zahlenformate oder die emotionale Relevanz der Inhalte variieren. Ob und wie stark sich dieser Domäneneffekt von der reinen Visualisierungskomplexität trennen lässt, ist bislang kaum systematisch untersucht worden. Die vorliegende Studie greift genau diese Lücke auf.

### 1.2 Zielsetzung

Diese Studie prüft, ob sich kognitive Beanspruchung systematisch zwischen drei Inhaltsdomänen unterscheidet, und ob Bearbeitungszeit den subjektiv empfundenen Aufwand zuverlässig abbildet. Physiologische Sensordaten (Pupillendurchmesser, Hautleitwert, Photoplethysmographie) werden ergänzend als Grundlage für weiterführende Analysen erhoben.

> *Unterscheidet sich die kognitive Beanspruchung bei der Exploration interaktiver Datenvisualisierungen je nach Inhaltsdomäne, und ist Bearbeitungszeit ein verlässlicher Indikator für kognitive Last?*

Nebenfragestellungen: Welche Domäne erzeugt die höchste Frustration? Wie hängen Bearbeitungszeit und die einzelnen NASA-TLX-Dimensionen zusammen?

---

## 2. Stand der Technik

Sweller (1988) belegt anhand von Problemlöseexperimenten, dass die begrenzte Kapazität des Arbeitsgedächtnisses konventionelle Lösungsstrategien (z. B. Means-Ends-Analyse) mit dem Aufbau von Schemata konkurrieren lässt. Die heute gebräuchliche Unterscheidung in intrinsische, extrinsische und lernbezogene ("germane") kognitive Last wurde erst in der Weiterentwicklung der Theorie eingeführt (Paas et al., 2003). Für Datenvisualisierungen ist vor allem die extrinsische Last relevant: Ein unübersichtliches Dashboard zwingt Nutzende, mehr Ressourcen in die Entschlüsselung der Darstellung zu investieren. Der NASA-TLX (Hart & Staveland, 1988) ist das meistgenutzte Instrument zur subjektiven Workload-Erfassung.

Drei physiologische Messverfahren gelten als etablierte kontinuierliche Indikatoren kognitiver Beanspruchung (Beatty, 1982; Dawson et al., 2007): Pupillometrie, Hautleitwert und Herzrate via Photoplethysmographie (PPG). Hautleitwert misst die elektrische Leitfähigkeit der Haut, die mit Erregung steigt. PPG misst Blutvolumenänderungen über Lichtabsorption. Alle drei Verfahren erfordern jedoch eine gesonderte Validierung gegenüber NASA-TLX-Scores.

Weniger klar ist die Befundlage zur Rolle der Domänenvertrautheit. Expertise-Forschung zu Diagrammlesekompetenz geht meist davon aus, dass Vorwissen die kognitive Last senkt, weil vertraute Strukturen schneller in bestehende Schemata eingeordnet werden können (Schema-Theorie, vgl. Paas et al., 2003). Empirische Arbeiten, die Vertrautheit und affektive Reaktionen (etwa Frustration) getrennt erfassen, sind jedoch selten, da meist nur die Bearbeitungsgeschwindigkeit als Erfolgsindikator herangezogen wird. Die vorliegende Studie prüft daher explizit, ob subjektive Vertrautheit und Frustration tatsächlich gegenläufig sind, wie die Schema-Theorie nahelegen würde.

---

## 3. Methodik

### 3.1 Versuchspersonen und Design

Die Experimentaldaten wurden im Rahmen eines bestehenden Versuchsaufbaus erhoben und dem Autor in anonymisierter Form (Trial-IDs statt Personendaten) zur Analyse bereitgestellt. Der eigene Beitrag umfasst ein Analyse-Tool (Python/Streamlit) zur explorativen Sichtung und tabellarischen Auswertung der TLX- und Sensordaten sowie die statistische Auswertung und Interpretation in Kapitel 4 und 5. Für Einwilligung und Datenschutz der physiologischen Messungen (Herzrate, Hautleitwert, Pupillometrie) ist die Ursprungserhebung verantwortlich. Diese Arbeit hatte auf die entsprechenden Unterlagen keinen Zugriff.

An der Studie nahmen N = 18 Personen teil (Convenience-Sample, Hochschulkontext). Demografische Angaben liegen für 17 vor, überwiegend jung (18–24 Jahre, 13 von 17), ausgeglichen nach Geschlecht (9/8), mehrheitlich im IT-Bereich (8 von 17). Die subjektive Domänenvertrautheit war für Stadtplanung am geringsten (M = 28,5), für Gaming am höchsten (M = 44,1, SD = 25,6), Gesundheit dazwischen (M = 40,4). Das Design war ein vollständiges Within-Subject-Design (5 Visualisierungstypen × 3 Domänen). Die Domänenreihenfolge wurde nach einem Lateinischen Quadrat balanciert. Die Reihenfolge der Visualisierungstypen (Timeline → Scatter → Combo → Heatmap → Dashboard) war für alle gleich.

Der Ablauf: Kalibrierung, 30s-Baseline, drei Domänenblöcke mit je fünf Aufgaben und anschließendem NASA-TLX. Gesamtdauer 45–60 Minuten. Die Baseline-Phase dient als Referenzzustand für die in 4.4 berichtete Zentrierung der Sensordaten. Sie wurde vor Beginn des ersten Domänenblocks erhoben, also vor jeder aufgabenbezogenen Beanspruchung.

### 3.2 Aufgaben und Visualisierungstypen

Die Domänen: Gaming (Spielerstatistiken), Gesundheit (Patientendaten), Stadtplanung (Infrastrukturdaten). Die Visualisierungstypen (Timeline, Scatter, Combo, Heatmap, Dashboard) unterschieden sich in ihrer angenommenen kognitiven Anforderung, von sequentiellem Ablesen (Timeline) bis zur Koordination mehrerer verknüpfter Diagramme (Dashboard). Die Reihenfolge war für alle Teilnehmenden identisch. Aussagen zur relativen Anforderung der Typen sind daher nicht von Lern-/Ermüdungseffekten trennbar (vgl. 5.3) und beruhen auf der theoretischen Einordnung aus Kap. 2, nicht auf empirischem Vergleich.

Der NASA-TLX (Raw-Version) wurde nach jedem Domänenblock erhoben (54 Datensätze gesamt). Es liegen keine Scores auf Diagrammtyp-Ebene vor. Die Raw-Version verzichtet, anders als die gewichtete Originalversion, auf paarweise Vergleiche zur Gewichtung der sechs Dimensionen. Dies verkürzt die Erhebung, verhindert aber eine individuelle Gewichtung je nachdem, welche Dimension für die jeweilige Person subjektiv am stärksten zur Gesamtbelastung beiträgt.

### 3.3 Messinstrumente und Datenvorverarbeitung

- **Shimmer3** (Handgelenk, 10 Hz): Hautleitwert, Herzrate (PPG), Beschleunigung/Gyroskop/Magnetometer.
- **Tobii Eye-Tracker** (remote, ~33 Hz): Blickpunkt, Pupillendurchmesser beidseitig.

Aus den Eventlogs wurden Start-/Endzeitstempel je Aufgabe extrahiert (15 Aufgabensegmente + ein Baseline-Segment pro Trial). Sampling-Lücken (>3.000 ms), doppelte Zeitstempel und Plausibilitätsverletzungen wurden automatisch geprüft. Die in Tabelle 2 (4.2) berichtete Bearbeitungszeit und die in Tabelle 3 (4.3) berichtete Korrelationsanalyse wurden über zwei unabhängige Event-Paarungslogiken aus denselben rohen Event-Logs berechnet, nicht über eine gemeinsame Pipeline. Zur Qualitätssicherung wurden beide Berechnungswege eigenständig aus den Rohdaten rekonstruiert und stimmten bis auf eine kleine, in 5.3 diskutierte Restdifferenz beim Stadt-Mittelwert überein.

---

## 4. Ergebnisse

### 4.1 NASA-TLX nach Domäne

**Tabelle 1: NASA-TLX-Scores nach Domäne (N = 18, Skala 0–100)**

| Dimension | Gaming M (SD) | Gesundheit M (SD) | Stadt M (SD) |
|---|---|---|---|
| Mentale Anforderung | 61,5 (25,5) | 62,6 (23,5) | 63,2 (21,9) |
| Körperliche Anforderung | 27,8 (27,9) | 22,5 (26,1) | 22,4 (26,6) |
| Zeitliche Anforderung | 28,9 (28,4) | 27,0 (32,5) | 25,6 (29,8) |
| Leistung | 41,4 (24,3) | 41,8 (18,6) | 49,7 (23,2) |
| Anstrengung | 51,2 (27,1) | 45,1 (22,1) | 46,3 (26,7) |
| Frustration | 47,4 (38,3) | 43,5 (37,6) | 36,8 (33,1) |

*(SDs als Stichproben-Standardabweichung berechnet. Geringe Abweichungen zu einer Populations-SD-Konvention sind rein rechnerischer Natur.)*

Die **mentale Anforderung** liegt in allen Domänen auf nahezu identischem Niveau. Die Differenz (Δ = 1,7) ist angesichts der Streuung (SD ≈ 22–26) klein und ohne Signifikanztest nicht von Rauschen zu unterscheiden. **Frustration** weist die stärkste domänenabhängige Variation auf (Gaming vs. Stadt: Δ = 10,6). Die übrigen Dimensionen zeigen ähnliche Muster über alle Domänen und werden nicht weiter differenziert.

**Abbildung 1: NASA-TLX-Dimensionen nach Domäne**

![Abbildung 1: NASA-TLX-Boxplot](figures/paper1_abb1_tlx_boxplot.png)

*Boxplots aller sechs NASA-TLX-Dimensionen je Domäne (N = 18). Median, Interquartilsabstand und Ausreißer.*

Abbildung 1 veranschaulicht die in Tabelle 1 berichtete Streuung: Die Kästen der mentalen Anforderung liegen für alle drei Domänen auf ähnlicher Höhe (der Boxplot zeigt hier Mediane, Tabelle 1 Mittelwerte, beide Kennzahlen zeichnen aber dasselbe Bild), während die Frustrations-Boxen deutlich unterschiedliche Mediane und breitere Spannweiten zeigen, insbesondere bei Gaming.

### 4.2 Bearbeitungszeit nach Domäne

**Tabelle 2: Bearbeitungszeit in Sekunden (269 Aufgaben; 1 Ausreißer ausgeschlossen)**

| Domäne | N | M (s) | SD (s) | Min | Max |
|---|---|---|---|---|---|
| Gaming | 90 | 69,6 | 38,5 | 7 | 214 |
| Gesundheit | 90 | 75,2 | 54,1 | 7 | 310 |
| Stadt | 89¹ | 68,7 | 32,3 | 16 | 164 |

¹ Ein Aufgabenmesswert (T-3, Stadt, 849 s = 14,2 min) wurde als Datenerfassungsstörung eingestuft und ausgeschlossen (N = 89 statt 90). Die übrigen Daten dieses Trials blieben in der Auswertung.

Gesundheits-Aufgaben dauerten im Schnitt am längsten und wiesen zugleich die höchste Variabilität auf (zu einer kleinen, ungeklärten Differenz bei der Rekonstruktion des Stadt-Mittelwerts vgl. 5.3).

### 4.3 Korrelation zwischen Bearbeitungszeit und NASA-TLX

Tabelle 3 stellt die Pearson-Korrelationen zwischen kumulierter Bearbeitungszeit pro Domäne und den NASA-TLX-Dimensionen dar. Die Analyse ist explorativ: Die einfachen Domänen-Korrelationen werden unten ohne p-Wert berichtet, da sie durch Pseudoreplikation verzerrt sind. Erst das nachfolgende Mixed-Model korrigiert dafür und liefert einen interpretierbaren p-Wert (s. u.). Nach Cohen (1988) entspricht r ≈ 0,5 einem großen Effekt.

**Tabelle 3: Pearson-Korrelationen Bearbeitungszeit × NASA-TLX**
*(N = 53 statt 54 Domänendurchläufe: Der von der Datenerfassungsstörung betroffene Durchlauf T-3/Stadt aus Tabelle 2 wurde hier vollständig ausgeschlossen. Grund: Der Ausreißer würde die kumulierte Domänendauer verzerren, anders als den dortigen Einzeltask-Mittelwert. Keine unabhängigen Beobachtungen, s. u.)*

| Domäne | r (Frustration) | r (Mentale Anf.) | r (Anstrengung) |
|---|---|---|---|
| Gaming | **0,56** | 0,16 | 0,08 |
| Gesundheit | **0,61** | 0,13 | 0,13 |
| Stadt | **0,48** | −0,26 | 0,08 |
| **Gesamt** | **0,56** | 0,03 | 0,09 |

Frustration zeigt den stärksten Zusammenhang (r = 0,56), während mentale Anforderung (r = 0,03) und Anstrengung (r = 0,09) kaum einen erkennen lassen.

**Abbildung 2: Bearbeitungszeit × NASA-TLX (Frustration und Mentale Anforderung)**

![Abbildung 2: Streudiagramm Bearbeitungszeit x TLX](figures/paper1_abb2_scatter_duration_tlx.png)

*Kumulierte Bearbeitungszeit pro Domänendurchlauf gegen Frustration (links) und mentale Anforderung (rechts), farblich nach Domäne, mit Regressionsgeraden je Domäne und gesamt (N = 53, ein Ausreißer ausgeschlossen).*

Abbildung 2 liefert einen Hinweis, der über die reinen r-Werte hinausgeht: Im linken Teilbild steigen die drei domänenspezifischen Regressionsgeraden für Frustration übereinstimmend mit der Bearbeitungszeit an, wenn auch mit unterschiedlicher Steigung, der positive Zusammenhang ist also nicht auf eine einzelne Domäne beschränkt. Im rechten Teilbild verlaufen die Regressionsgeraden zur mentalen Anforderung dagegen uneinheitlich in unterschiedliche Richtungen, was erklärt, warum sich über alle Domänen hinweg kein Gesamttrend ergibt.

Diese einfachen Domänen-Korrelationen sind jedoch durch Pseudoreplikation angreifbar: Da die 53 Domänendurchläufe aus nur 18 Personen stammen (within-subject, Pseudoreplikation), wurde der Effekt zusätzlich innerhalb der Personen zentriert und per personen-geclustertem Bootstrap (5.000 Resamples, NumPy) sowie einem vollständigen Mixed-Model (Random Intercept pro Person, Python, statsmodels `MixedLM`) geprüft:

| Dimension | r (unkorrigiert) | 95%-CI | r (zentriert) | 95%-CI | Mixed-Model p |
|---|---|---|---|---|---|
| Frustration | 0,56 | [0,30, 0,78] | **0,52** | **[0,37, 0,71]** | **<0,0001** |
| Mentale Anforderung | 0,03 | [−0,37, 0,51] | 0,15 | [−0,10, 0,42] | 0,569 |
| Anstrengung | 0,09 | [−0,27, 0,45] | 0,00 | [−0,36, 0,39] | 0,949 |

Beide Korrekturverfahren bestätigen übereinstimmend, dass Frustration nicht auf Personenunterschiede zurückzuführen ist: Der Effekt bleibt nach Zentrierung nahezu unverändert und ist im Mixed-Model hoch signifikant (Slope = 0,133, 95%-CI [0,073, 0,193]). Für mentale Anforderung/Anstrengung zeigt sich in keinem Verfahren ein belastbarer Effekt. Alle Konfidenzintervalle bleiben bei N = 18–53 breit.

### 4.4 Sensordaten: Deskriptiver Überblick

Physiologische Sensordaten (Pupillendurchmesser, Hautleitwert, PPG) liegen für alle 18 Trials vollständig vor (Tabelle 4). Da dieser Abschnitt keine der beiden Forschungsfragen beantwortet, wird er hier nur knapp dokumentiert. Für 17 von 18 Trials liegt eine Baseline-Zentrierung pro Domäne vor. Bei T-10 fehlt lediglich das Baseline-Segment, die übrigen Rohdaten dieses Trials sind vollständig. Nach dieser Zentrierung lässt sich weder bei Pupillendurchmesser noch bei Hautleitwert ein domänenspezifisches Muster erkennen (Deltas nahe null), anders als bei Frustration in Tabelle 1. Ob dies an mangelnder Sensitivität der Maße oder einer echten Entkoppelung physiologischer und subjektiver Reaktion liegt, lässt sich mit diesen Daten nicht klären.

**Tabelle 4: Deskriptive Statistik ausgewählter Sensorkanäle**

| Kanal | Einheit | Ø | SD | Min | Max |
|---|---|---|---|---|---|
| Pupillendurchmesser links | mm | 4,58 | 0,80 | 1,51 | 6,90 |
| Pupillendurchmesser rechts | mm | 4,59 | 0,83 | 1,78 | 7,38 |
| Hautleitwert (GSR) | µS | 2,72 | 4,88 | 0,02 | 24,77 |
| PPG-Rohsignal | mV | 182,9 | 35,1 | 60,1 | 236,6 |

---

## 5. Diskussion

### 5.1 Domänenmuster: stabile mentale Last, domänenspezifische Frustration

Die mentale Anforderung bleibt über alle Domänen praktisch konstant (Δ = 1,7 zwischen den Extremwerten). Weder die Domäne selbst noch die in 3.1 erhobene Domänenvertrautheit scheinen sie zu beeinflussen. Das widerspricht der in Kap. 2 skizzierten Schema-Theorie, wonach Vorwissen die Verarbeitung entlasten sollte — stattdessen scheint die Visualisierungsform selbst ein stärkerer Treiber der mentalen Last zu sein als der dargestellte Inhalt. Diese Interpretation kann durch die feste Reihenfolge der Visualisierungstypen (3.2) allerdings nicht kausal abgesichert werden. Für die Gestaltungspraxis bedeutet das, dass Fachkompetenz allein die kognitive Beanspruchung nicht reduziert. Die extrinsische Last muss stattdessen über das Design selbst minimiert werden.

Frustration verhält sich gegenläufig zu dieser Stabilität und folgt auch nicht der erwarteten Vertrautheits-Logik: Gaming-Aufgaben erzeugten die höchste Frustration bei gleichzeitig höchster subjektiver Vertrautheit (M = 44,1), Stadt-Aufgaben die niedrigste bei geringster Vertrautheit (M = 28,5). Hohe Domänenvertrautheit schützt demnach nicht vor Frustration. Welcher Mechanismus dahintersteht, etwa semantisch komplexe, spieldomänenspezifische Metriken, lässt sich mit diesem Datensatz nicht klären. Frustration und mentale Anforderung erweisen sich damit als empirisch trennbare Konstrukte, die in künftigen Studien nicht länger synonym als "kognitive Last" behandelt werden sollten.

### 5.2 Bearbeitungszeit als partieller Belastungsindikator

Bearbeitungszeit ist kein allgemeiner Proxy für kognitive Beanspruchung: Sie korreliert mit Frustration, nicht mit mentaler Anforderung oder Anstrengung. Die Korrelation legt zudem keine Wirkrichtung fest. Ebenso plausibel wie "Dauer erzeugt Frustration" ist die umgekehrte Lesart, dass Frustration zu Herumprobieren und damit längerer Dauer führt, etwa weil Aufgaben schwer verständlich sind. Das Querschnittsdesign kann nicht zwischen beiden unterscheiden. Dafür wären zeitlich aufgelöste Messungen nötig, etwa eine kontinuierliche Erfassung von Frustrationsindikatoren während der Aufgabenbearbeitung, beispielsweise über Verhaltensmarker wie wiederholtes Zurückspringen zwischen Diagrammelementen, statt einer retrospektiven Einzelbewertung am Blockende.

Studien, die Bearbeitungszeit als kognitive Last interpretieren, messen wahrscheinlich primär aufgabenspezifische Schwierigkeit und affektive Reaktion. Für die Praxis bedeutet das, dass eine lange Bearbeitungsdauer nicht automatisch als Hinweis auf hohe mentale Beanspruchung gewertet werden sollte, sondern eher als Signal für eine mögliche Frustrationsquelle im Interface, die gezielt untersucht werden sollte.

### 5.3 Einschränkungen

**Stichprobengröße:** N = 18 liegt unterhalb der für parametrische Tests empfohlenen Mindeststärke. Abgesehen vom Mixed-Model in 4.3 wurden keine weiteren formalen Signifikanztests durchgeführt. Für eine verlässliche Absicherung von Effekten dieser Stärke (r ≈ 0,5–0,6, 80 % Teststärke) wären ca. 19–32 unabhängige **Personen** nötig. Mehr Domänendurchläufe pro Person ersetzen das nicht. Diese Schätzung beruht auf der Fisher-z-Transformation, einem Standardverfahren zur Stichprobengrößenplanung bei Korrelationen.

**Pseudoreplikation:** Trotz der in 4.3 gezeigten Bestätigung durch Zentrierung und Mixed-Model bleibt N = 18 Personen die begrenzende Größe. Auch die Konfidenzintervalle des vollständigen Modells sind vergleichsweise breit.

**Rekonstruktionsdifferenz:** Die in Tabelle 2 berichteten Mittelwerte wurden anhand der rohen Task-Events nachvollzogen. Bis auf eine kleine Abweichung beim Stadt-Mittelwert (~2 %) stimmten alle Werte überein. Die Ursache dieser Restdifferenz ließ sich nicht abschließend klären.

**Visualisierungsreihenfolge:** Die feste Reihenfolge der Visualisierungstypen erlaubt keine von Lerneffekten getrennte Aussage über deren relative Anforderung. Da NASA-TLX nur pro Domänenblock erhoben wurde, sind Visualisierungstyp-Effekte generell nicht prüfbar.

**Fehlende Sensor-TLX-Korrelation:** Die Sensordaten wurden, abgesehen vom baseline-korrigierten Domänenvergleich, nicht mit TLX-Scores korreliert.

**Selbstauskunfts-Bias:** Die Domänenvertrautheit wurde nur über Selbsteinschätzung erfasst (Verzerrungsrisiko, z. B. Dunning-Kruger-Effekt).

**Retrospektive Erhebung:** Der NASA-TLX wurde ausschließlich retrospektiv am Ende jedes Domänenblocks erhoben, nicht kontinuierlich während der Aufgabenbearbeitung. Kurzfristige Belastungsspitzen einzelner Aufgaben können dadurch im Blockmittel untergehen.

---

## 6. Fazit

Kognitive Last bei der Exploration von Datenvisualisierungen lässt sich nicht auf eine einzige Kennzahl reduzieren. Mentale Beanspruchung und Frustration folgen unterschiedlichen Mustern und brauchen unterschiedliche Erklärungsmodelle. Diese Befunde sind angesichts von N = 18 Personen explorativ und ohne formale Signifikanztests (bis auf das Mixed-Model in 4.3) zu verstehen. Wer nur Bearbeitungszeit oder einen globalen NASA-TLX-Gesamtwert erhebt, verdeckt genau diese Trennung. Die getrennte Betrachtung war hier erst durch zwei unabhängige Bestätigungsverfahren methodisch absicherbar: einen personen-geclusterten Bootstrap und ein vollständiges Mixed-Model, die beide übereinstimmend zeigen, dass Frustration nicht auf Personenunterschiede zurückzuführen ist.

Als Messhinweis für die Praxis folgt daraus, dass lange Bearbeitungsdauer als Signal für mögliche Frustrationsquellen im Interface gelesen werden sollte, nicht vorschnell als Beleg für hohe mentale Beanspruchung. Für die Forschung folgt ein doppelter Bedarf, nämlich eine Replikation mit größerer, unabhängiger Stichprobe sowie zeitlich aufgelöste Messverfahren, die die Kausalrichtung zwischen Frustration und Dauer tatsächlich prüfen können. Diese Frage lässt das vorliegende Querschnittsdesign offen.

---

## Literatur

Beatty, J. (1982). Task-evoked pupillary responses, processing load, and the structure of processing resources. *Psychological Bulletin, 91*(2), 276–292.

Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.

Dawson, M. E., Schell, A. M., & Filion, D. L. (2007). The electrodermal system. In *Handbook of psychophysiology* (3rd ed., pp. 159–181). Cambridge University Press.

Hart, S. G., & Staveland, L. E. (1988). Development of NASA-TLX. *Advances in Psychology, 52*, 139–183.

Paas, F., Renkl, A., & Sweller, J. (2003). Cognitive load theory and instructional design. *Educational Psychologist, 38*(1), 1–4.

Sweller, J. (1988). Cognitive load during problem solving. *Cognitive Science, 12*(2), 257–285.
