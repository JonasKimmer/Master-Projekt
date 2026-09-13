# Automatisierte Analyse struktureller Webkomplexität: Merkmalsextraktion und Klassifikation gecrawlter Webseiten

**Jonas Kimmer**  
**[BITTE VOR ABGABE ERGÄNZEN: Hochschule · Studiengang · Matrikelnummer · Betreuer:in · Abgabedatum]** · 2026

---

## Zusammenfassung

Automatisierte Verfahren zur Einschätzung von Website-Komplexität beschränken sich meist auf Einzelmetriken und sind selten offen anpassbar. Diese Arbeit untersucht, ob sich die strukturelle Komplexität einzelner Webseiten automatisiert messen und klassifizieren lässt, und ob ein mehrdimensionales Merkmalsmodell dabei mehr leistet als eine Einzelmetrik. Auf Basis selbst gecrawlter, ungerenderter HTML-Daten von drei öffentlichen Websites (bpb.de, hs-rm.de, wiesbaden.de, N = 47 Unterseiten) extrahierte ein modulares Analyse-Tool sechs strukturelle Merkmale je Seite. Ein K-Means-Clustering trennt die Seiten nur mäßig und ist nur teilweise mit der Website-Zugehörigkeit konfundiert. Eine Reihe von Robustheitsprüfungen relativiert das mehrdimensionale Modell. Die gewählte Cluster-Anzahl ist nicht datenoptimal. Eine einzelne Metrik, hier die Linkanzahl, erzeugt intern besser getrennte Cluster als das volle Sechs-Merkmale-Modell, auch nach Dekorrelation redundanter Merkmale. Die scheinbare Bedeutung zweier Merkmale erweist sich als Verfahrensartefakt, und die Kreuzvalidierung bleibt deutlich unter der optimistischen Einzelschätzung. Ein unabhängiges externes Kriterium, die HTTP-Antwortzeit, bestätigt weder Clusterstruktur noch die wichtigsten Merkmale. Die Forschungsfrage ist damit im Sinne technischer Machbarkeit zu bejahen, im Sinne einer robusten, mehrwertigen und extern validierten Komplexitätsmessung jedoch nicht. Alle Kennzahlen sind aus dem versionskontrollierten Projekt reproduzierbar.

**Schlüsselwörter:** Webkomplexität, DOM-Analyse, HTML-Parsing, Clustering, Feature-Extraktion, Permutation-Importance, Cross-Validation

---

## Abbildungsverzeichnis

- **Abbildung 1:** DOM-Tiefe × Linkanzahl nach Cluster (Abschnitt 4.2)

## Tabellenverzeichnis

- **Tabelle 1:** Merkmalsverteilung, N = 47 Seiten (Abschnitt 4.1)
- **Tabelle 2:** Cluster-Charakteristika (Abschnitt 4.2)
- **Tabelle 3:** Cluster-Verteilung nach Website (Abschnitt 4.2)
- **Tabelle 4:** Feature-Importance: MDI vs. Permutation (Abschnitt 4.3)
- **Tabelle 5:** Merkmals-Mittelwerte je Website (Abschnitt 4.4)
- **Tabelle 6:** Korrelation Antwortzeit × Strukturmerkmale (Abschnitt 4.6)
- **Tabelle 7:** Antwortzeit nach Cluster und Website (Abschnitt 4.6)


---

## 1. Einleitung

### 1.1 Motivation und Problemstellung

Websites unterscheiden sich in ihrer strukturellen Komplexität teils stark: Einfache Landingpages stehen neben umfangreichen Portalen mit tiefen DOM-Hierarchien und vielfältigen interaktiven Elementen. Diese Unterschiede werden in der Praxis mit Ladezeiten, Barrierefreiheit, Wartbarkeit und Nutzererfahrung in Verbindung gebracht, eine objektive und über Websites hinweg vergleichbare Einschätzung ist für Webentwickler, UX-Designer und Qualitätssicherungsteams daher wertvoll. Manuelle Bewertungen sind dafür aufwendig, subjektiv und schlecht skalierbar, ein Vergleich über mehrere Websites oder über Zeit ist so kaum möglich. Bestehende automatisierte Ansätze beschränken sich zudem häufig auf Einzelmetriken wie die Seitenanzahl, ohne DOM-Tiefe oder die Verteilung interaktiver Elemente zu berücksichtigen, und viele Analyse-Tools sind geschlossen, cloudbasiert und nicht anpassbar. Ein offenes, modulares und mehrdimensional messendes Werkzeug fehlt bisher.

### 1.2 Zielsetzung

Vorgestellt wird ein modulares Analyse-Tool, das gecrawlte Website-Daten automatisch einliest und pro Seite strukturelle Merkmale extrahiert. Daraus ergibt sich die zentrale Forschungsfrage:

> *Lässt sich die strukturelle Komplexität einzelner Webseiten anhand automatisiert extrahierter Merkmale messen und klassifizieren, ohne manuelle Annotation, und bietet ein mehrdimensionales Merkmalsmodell dabei einen belastbaren Mehrwert gegenüber einer Einzelmetrik?*

Drei Nebenfragen schärfen sie: Welche Merkmale sind die stärksten Komplexitätsindikatoren? Hält diese Einordnung einer methodenkritischen Prüfung stand? Ist die gewählte Cluster-Anzahl datengetrieben begründbar?

---

## 2. Stand der Technik

Webkomplexität ist kein einheitlich definiertes Konzept. Die breiteste empirische Grundlage stammt von Ivory und Hearst (2002), die 157 quantitative Maße untersuchten, von Text-, Link- und Grafikelementen über Formatierung bis zur Seiten- und Site-Architektur, und belegten, dass sich solche automatisiert berechenbaren Seitenmerkmale als Prädiktoren für die von Expert:innen wahrgenommene Seitenqualität eignen. Zu den am leichtesten erfassbaren zählen Strukturmerkmale des Document Object Model (DOM): Seine Baumstruktur lässt sich durch rekursives Traversieren des HTML-Quelltexts effizient ausmessen, Tiefe und Knotenanzahl gelten als zentrale Indikatoren struktureller Komplexität.

Die automatische Klassifikation von Webseiten nach Typ oder Funktion ist ein etabliertes Anwendungsfeld im Web Mining. Qi und Davison (2009) geben einen Überblick über die dabei verwendeten Merkmalsfamilien (Inhalt, Links, Struktur, URL) und Verfahren. Unüberwachte Verfahren wie K-Means-Clustering eignen sich besonders, wenn Seitentypen erst aus den Daten heraus identifiziert werden sollen.

Random-Forest-Klassifikatoren haben sich für tabellarische Feature-Matrizen als robuste Methode bewährt (Breiman, 2001). Ihre Feature-Importance lässt Rückschlüsse darauf zu, welche Merkmale die Klassifikation primär tragen. Werden die Labels jedoch durch ein vorheriges Clustering erzeugt, quantifiziert die Importance nur die interne Konsistenz der Clusterstruktur, nicht die externe Validität gegenüber einer unabhängigen Zielvariable. Zudem ist die Standard-Feature-Importance von Random Forests (Mean Decrease Impurity) bekanntermaßen zugunsten kontinuierlicher Merkmale mit vielen eindeutigen Werten verzerrt. Permutation-Importance gilt als robusteres Gegenstück.

Messwertbasierte Arbeiten verknüpfen Komplexität mit Außenkriterien: Butkiewicz et al. (2011) entwickelten aus Messungen realer Seiten Metriken für Inhalts- und Strukturkomplexität und untersuchten deren Zusammenhang mit der Ladeperformance. Ihre Befunde legen nahe, dass Seitenkomplexität mehrdimensional erfasst werden sollte. Chen (2018) vertritt demgegenüber den Outdegree einer Seite als alleiniges Komplexitätsmaß und optimiert Website-Struktur durch Link-Reduktion.

Jenseits der Strukturmerkmale untersucht die HCI-Forschung die *wahrgenommene* Komplexität. Tuch et al. (2012) zeigen experimentell, dass visuelle Komplexität und Prototypikalität die Ersturteile von Nutzenden prägen, und Miniukovich und De Angeli (2014) operationalisieren visuelle Komplexität rechnerisch. Struktur- und Wahrnehmungsmaße laufen damit nebeneinander. Ob sie dieselbe zugrundeliegende Dimension erfassen, ist ohne Erhebung von Nutzurteilen nicht entscheidbar.

---

## 3. Methodik

### 3.1 Datenbasis

Die Webcrawler-Daten wurden im Rahmen dieser Arbeit selbst erhoben. Der Beitrag umfasst ein modulares Analyse-Tool in Python mit Streamlit-Oberfläche, einen robots.txt-konformen Crawler zur Datenerhebung sowie die statistische Auswertung. Grundlage sind drei öffentliche Websites unterschiedlicher Gattung mit insgesamt 47 Unterseiten: das redaktionelle Informationsportal bpb.de der Bundeszentrale für politische Bildung mit 20 Unterseiten, die Hochschul-Website hs-rm.de mit 15 Unterseiten und das Bürger- und Verwaltungsportal wiesbaden.de mit 12 Unterseiten.

Der Crawler durchläuft Websites breit-zuerst innerhalb derselben Domain, respektiert die robots.txt und speichert pro Seite HTML-Quelltext, sichtbaren Text, Links, Formulare und Medienelemente als strukturierte JSON-Dateien (Erhebungszeitpunkt: 8. August 2026). Screenshots dienen nur der Ansicht und gehen nicht in die Merkmale ein. Für die Interpretation folgenreich ist, dass die Analyse auf dem ungerenderten HTML ohne JavaScript-Ausführung beruht: Bei bpb.de enthält keines der 20 Dokumente ein `<img>`-Tag, weil die Bilder erst client-seitig nachgeladen werden (`media_count` ist dadurch durchgängig 0). Bei wiesbaden.de fehlt jedes `<form>`-Element, weil das Formular selbst in einem externen Verwaltungsportal liegt, auf das nur verlinkt wird. Warum wiesbaden.de bei 12 Seiten endete, ob durch das Seitenlimit oder eine erschöpfte Warteschlange, lässt sich aus den Artefakten nicht mehr sagen.

### 3.2 Tool, Merkmale und Analyseverfahren

Das Analyse-Tool ist in Python implementiert und besitzt eine Streamlit-Oberfläche. Es liest Website-Ordner mit strukturierten JSON-Repräsentationen des DOM ein und entkoppelt Loader und Feature-Berechnung über typisierte Datenklassen. Pro Seite werden sechs strukturelle Merkmale berechnet:

| Merkmal | Beschreibung |
|---|---|
| link_count | Anzahl aller Link-Elemente (`<a href>`) der Seite, inkl. interner Navigation |
| form_count | Anzahl `<form>`-Elemente |
| media_count | Anzahl Medienelemente (Bilder, Videos) |
| text_length | Zeichenanzahl des sichtbaren Texts |
| dom_depth | Maximale Tiefe des DOM-Baums |
| dom_nodes | Gesamtanzahl der DOM-Knoten |

**Clustering:** Clusterung per K-Means (k = 3) auf z-standardisierten Merkmalen, zur Einordnung zusätzlich ein Scan über k = 2 bis 6. Die Trennschärfe misst der Silhouette-Score, wobei Werte über 0,5 als gute Trennung gelten (Rousseeuw, 1987). Ein Bootstrap mit 1.000 Stichproben schätzt die Unsicherheit des Scores. Wie stark die Cluster mit der Website-Zugehörigkeit zusammenfallen, misst der Adjusted Rand Index (ARI; Hubert & Arabie, 1985), bei dem 0 Zufallsniveau und 1 völlige Übereinstimmung bedeutet.

**Merkmalswichtigkeit und Klassifikation:** Ein Random Forest mit 100 Bäumen lernt, die Cluster den Seiten wiederzuzuordnen, und zwei Maße zeigen, welche Merkmale ihn dabei tragen. Die übliche Wichtigkeit (Mean Decrease Impurity) fällt bei Merkmalen mit vielen verschiedenen Werten systematisch zu hoch aus, die Permutationswichtigkeit, die misst, wie sehr sich das Modell verschlechtert, wenn ein Merkmal durchwürfelt wird, gilt als robusteres Gegenstück. Wie gut die Zuordnung gelingt, wird an einem einfachen 75/25-Split und an 5-facher Kreuzvalidierung verglichen, bei der das Modell fünfmal auf vier Fünfteln der Daten trainiert und am jeweils letzten Fünftel geprüft wird.

**Robustheit:** Gegen rein zufällige Lösungen ist das Clustering durch 50 Wiederholungen mit anderen Zufallssaaten abgesichert, verglichen als ARI zur Referenzlösung. Das prüft die algorithmische, nicht die inhaltliche Stabilität. Eine Baseline wiederholt das Clustering nur mit dem einzelnen Merkmal `link_count`, zwei Varianten ergänzen den Check gegen Rechtsschiefe und Merkmalsredundanz (log-transformierte bzw. dekorrelierte Merkmale).

**Externes Kriterium:** Als Außenkriterium dient die HTTP-Antwortzeit aller 47 Seiten, jeweils der Median aus drei Messungen. Sie erfasst nur die Serverantwort, nicht die vollständige browserseitige Ladezeit, ist dafür aber von den sechs Strukturmerkmalen unabhängig.

**Reproduzierbarkeit:** Alle Auswertungen erzeugt das Skript `check_web_analysis.py` aus der versionierten Merkmalsdatei, Zufallsentscheidungen sind dort mit festen Saaten fixiert.

---

## 4. Ergebnisse

### 4.1 Merkmalsverteilung über alle Seiten

Tabelle 1 zeigt, wie die sechs strukturellen Merkmale über die 47 Seiten verteilt sind.

**Tabelle 1: Merkmalsverteilung (N = 47 Seiten)**

| Merkmal | M | SD | Min | Max |
|---|---|---|---|---|
| link_count | 170,0 | 169,3 | 44 | 1.187 |
| form_count | 0,19 | 0,45 | 0 | 2 |
| media_count | 6,02 | 9,60 | 0 | 35 |
| text_length | 8.792 | 10.845 | 1.258 | 54.453 |
| dom_depth | 16,36 | 2,10 | 14 | 21 |
| dom_nodes | 1.111 | 923 | 521 | 4.733 |

Zwei Merkmale sind durch die Erfassungsartefakte aus 3.1 systematisch nach unten verzerrt: `media_count`, weil bpb.de durchgängig 0 liefert, und `form_count`, weil wiesbaden.de keine Formulare liefert. Bei `link_count` und `text_length` treiben umgekehrt wenige große Übersichtsseiten die Mittelwerte nach oben, die Verteilungen sind ausgeprägt rechtsschief.

### 4.2 Clustering: Automatisch identifizierte Seitentypen

Die Clusteranalyse teilt die 47 Seiten in drei Cluster, deren Charakteristika Tabelle 2 zeigt und deren Zusammensetzung nach Websites Tabelle 3. Der Silhouette-Score von 0,433 liegt unterhalb der 0,5-Schwelle für einen „guten“ Trennungswert.

**Tabelle 2: Cluster-Charakteristika (Mittelwerte je Cluster)**

| Cluster | N | Links M | DOM-Tiefe M | Text M | Medien M | Typ (post-hoc) |
|---|---|---|---|---|---|---|
| 0 | 30 | 107,7 | 16,9 | 4.084,6 | 2,2 | Kompakte Seiten |
| 1 | 6 | 395,0 | 15,7 | 28.589,2 | 0,0 | Hub-/Übersichtsseiten |
| 2 | 11 | 217,3 | 15,3 | 10.831,3 | 19,6 | Medienreiche Seiten |

Die Bezeichnungen sind post-hoc vergebene Hilfsbegriffe, keine validierten Kategorien. Ein Cluster mit hohem `form_count` ergibt sich nicht, eine Folge des Erfassungsartefakts.

Tabelle 3 kreuzt die Cluster-Zugehörigkeit mit der Website-Zugehörigkeit.

**Tabelle 3: Cluster-Verteilung nach Website**

| Website | Cluster 0 | Cluster 1 | Cluster 2 | Gesamt |
|---|---|---|---|---|
| bpb.de | 14 | 6 | 0 | 20 |
| hs-rm.de | 4 | 0 | 11 | 15 |
| wiesbaden.de | 12 | 0 | 0 | 12 |
| **Gesamt** | **30** | **6** | **11** | **47** |

Der ARI von 0,243 zeigt eine partielle Konfundierung: Cluster 1 und 2 bestehen ausschließlich aus bpb.de- beziehungsweise hs-rm.de-Seiten, nur Cluster 0 vereint alle drei Websites.

**Abbildung 1: DOM-Tiefe × Linkanzahl nach Cluster**

![Abbildung 1: Cluster Scatter](figures/paper2_abb2_cluster_scatter_v2.png)

*Scatter-Plot der 47 Seiten, eingefärbt nach Cluster. ★ markiert das jeweilige Clusterzentrum.*

Abbildung 1 stellt diese Konfundierung räumlich dar. Die beiden website-reinen Cluster bilden im Zentrum klar getrennte Punktwolken, die sich in den Randbereichen überlappen. Cluster 0 verteilt sich über weite Teile des Diagramms.

### 4.3 Feature-Importance und Klassifikationsgüte

Der einzelne 75/25-Split erreicht eine Genauigkeit von 1,000, die 5-fache Kreuzvalidierung im Mittel nur 0,831 (Folds 0,556 bis 1,000). Stratifiziert liegt das Mittel bei 0,936, die schwachen Folds spiegeln also vor allem die Cluster-Unbalanciertheit wider. Die Cluster-Labels sind aus den Merkmalen überwiegend rekonstruierbar, der Einzelwert bleibt eine optimistische Punktschätzung.

Tabelle 4 stellt die beiden Wichtigkeitsmaße gegenüber.

**Tabelle 4: Feature-Importance (MDI vs. Permutation-Importance)** *(Reproduktion: `check_web_analysis.py`, Permutation mit dokumentiertem Seed)*

| Merkmal | MDI | Permutation-Importance |
|---|---|---|
| dom_nodes | 0,254 | 0,099 |
| media_count | 0,180 | 0,056 |
| link_count | 0,225 | 0,054 |
| form_count | 0,086 | 0,005 |
| text_length | 0,176 | **0,000** |
| dom_depth | 0,078 | **0,000** |

`text_length` und `dom_depth` erscheinen unter MDI als relevant, ihre Permutation-Importance beträgt jedoch 0,000. Bei `text_length` passt das zum bekannten MDI-Bias zugunsten merkmalsreicher Werte, bei `dom_depth` mit nur 8 verschiedenen Werten reicht er als Erklärung nicht aus. `dom_nodes` und `link_count` bleiben unter beiden Methoden am wichtigsten. In der Korrelationsmatrix hängen `link_count`, `text_length` und `dom_nodes` stark zusammen (r = 0,72 bis 0,81), `dom_depth` mit keinem anderen Merkmal..

### 4.4 Website-Vergleich auf Aggregatniveau

Tabelle 5 vergleicht die Merkmals-Mittelwerte auf Website-Ebene.

**Tabelle 5: Merkmals-Mittelwerte je Website**

| Merkmal | bpb.de (N=20) | hs-rm.de (N=15) | wiesbaden.de (N=12) |
|---|---|---|---|
| link_count M | 206,6 | 210,5 | 58,6 |
| form_count M | 0,0 | 0,6 | 0,0 |
| media_count M | 0,0 | 18,3 | 0,8 |
| text_length M | 11.639,6 | 9.813,7 | 2.768,2 |
| dom_depth M | 15,3 | 16,0 | 18,6 |
| dom_nodes M | 1.461,2 | 998,7 | 668,3 |

Keine der drei Websites ist in allen sechs Merkmalen führend: bpb.de hat die höchste Textmenge und DOM-Knotenanzahl, hs-rm.de die höchste Linkanzahl, wiesbaden.de die größte DOM-Tiefe. Auffällig ist das Profil von wiesbaden.de mit der **geringsten Knotenzahl (668) bei gleichzeitig höchster DOM-Tiefe (18,6)**. Die `media_count`-Werte von bpb.de und die `form_count`-Werte von wiesbaden.de sind durch die in 3.1 beschriebenen Erfassungsartefakte nach unten verzerrt und nicht als reale Abwesenheit zu lesen..

### 4.5 Robustheitsprüfungen: k-Wahl, Stabilität, Baseline

Der k-Scan über k = 2 bis 6 liefert Silhouette-Scores von 0,466 (k = 2), 0,446 (k = 4), 0,436 (k = 5) und 0,480 (k = 6), gegenüber 0,433 bei k = 3. k = 3 liefert also nicht den höchsten Score. Die Wahl folgt der Vergleichbarkeit mit der dreiteiligen Datenbasis, nicht der datengetriebenen Optimierung.

**Cluster-Stabilität:** Über 50 Wiederholungen mit anderen Zufallssaaten ergibt sich ein mittlerer ARI von 0,986. Die Lösung ist damit algorithmisch stabil.

**Silhouette-Bootstrap:** 1.000 Resamples ergeben einen Mittelwert von 0,472 (95%-CI [0,380, 0,566]). Der Punktschätzer 0,433 liegt am unteren Rand, die 0,5-Schwelle wird auch im Mittel nicht sicher erreicht.

**Baseline-Vergleich:** Clustering nur auf `link_count` erzielt einen Silhouette-Score von 0,667, deutlich höher als das Sechs-Merkmale-Modell (0,433). Beide Lösungen stimmen nur mäßig überein (ARI = 0,527). In dieser Stichprobe erzeugt die Einzelmetrik eine klarer abgegrenzte Clusterstruktur als der vollständige Merkmalsvektor.

**Dekorrelations-Analyse:** Die Korrelationsmatrix (4.3) legt nahe, dass drei der sechs Merkmale überwiegend dieselbe „Umfang"-Dimension messen (`text_length` und `dom_nodes` korrelieren mit r = 0,81 bzw. 0,72 mit `link_count`). Wird das Clustering auf den dekorrelierten Satz `link_count`, `dom_depth`, `media_count`, `form_count` beschränkt, steigt der Silhouette-Score auf **0,500** und bleibt der ursprünglichen Lösung strukturell ähnlich. Zwei Einschränkungen bleiben: 0,500 liegt weiterhin unterhalb der Einzelmetrik-Baseline (0,667), und die Lösung isoliert die extremste bpb.de-Seite als **Single-Page-Cluster** (35/11/1).

**Log-Transform-Variante:** Auf log1p-transformierten, z-standardisierten Merkmalen (gegen die Rechtsschiefe von `link_count` und `text_length`) steigt der Silhouette-Score nur leicht auf 0,462, und auch die `link_count`-Baseline bleibt bei 0,667. Die Rechtsschiefe erklärt damit praktisch nichts des Baseline-Vorteils, das zentrale Robustheitsproblem ist die Merkmalsredundanz.

### 4.6 Externes Kriterium: Zusammenhang mit realer Antwortzeit

Alle bisherigen Kennzahlen bewerten, wie gut die sechs Merkmale sich selbst erklären. Das ist ein internes Gütekriterium. Als unabhängige Gegenprobe wurde die HTTP-Antwortzeit aller 47 Seiten gemessen und gegen Strukturmerkmale und Clusterzugehörigkeit getestet.

*Provenienz-Hinweis: Die Einzelmessungen (3 Wiederholungen je Seite, Median) wurden nicht als Datei archiviert und sind nicht mehr auffindbar. Die folgenden Werte stammen aus der verlorenen Messung und lassen sich aus dem Projektstand nicht erneut prüfen. Sie werden der Vollständigkeit halber berichtet und als nicht reproduzierbar gekennzeichnet.*

Tabelle 6 zeigt die Korrelationen der Antwortzeit mit den Strukturmerkmalen.

**Tabelle 6: Korrelation Antwortzeit × Strukturmerkmale**

| Merkmal | r | p |
|---|---|---|
| dom_depth | 0,289 | **0,049** |
| link_count | −0,199 | 0,179 |
| media_count | −0,191 | 0,200 |
| text_length | −0,188 | 0,206 |
| dom_nodes | −0,184 | 0,216 |
| form_count | 0,147 | 0,325 |

Nur `dom_depth` weist einen schwachen, gerade noch signifikanten Zusammenhang auf, der die Bonferroni-Korrektur für sechs Tests jedoch nicht übersteht. Ein abgesicherter Effekt ist das nicht. Auch die wichtigsten Merkmale `dom_nodes` und `link_count` zeigen keinen signifikanten Zusammenhang.

Tabelle 7 stellt die Antwortzeiten nach Cluster und Website gegenüber.

**Tabelle 7: Antwortzeit nach Cluster und Website**

| Gruppe | M (s) | SD | N |
|---|---|---|---|
| Cluster 0 (Kompakte Seiten) | 0,133 | 0,065 | 30 |
| Cluster 1 (Hub-/Übersichtsseiten) | 0,093 | 0,008 | 6 |
| Cluster 2 (Medienreiche Seiten) | 0,114 | 0,071 | 11 |
| bpb.de | 0,102 | 0,041 | 20 |
| hs-rm.de | 0,106 | 0,061 | 15 |
| wiesbaden.de | 0,182 | 0,064 | 12 |

Zwischen den drei Clustern ist der Mittelwertunterschied nicht signifikant (ANOVA, p = 0,319). wiesbaden.de antwortet im Mittel am langsamsten. Clusterstruktur und wichtigste Merkmale zeigen damit keinen signifikanten Zusammenhang mit dem Außenkriterium, wobei die reine Server-Antwortzeit nur einen Teil der erlebten Ladezeit abbildet.

---

## 5. Diskussion

### 5.1 Strukturelle Merkmale als Komplexitätsindikatoren

Dass gerade `link_count` und `dom_nodes` die Cluster tragen, passt zum Befund von Ivory und Hearst (2002), dass quantitative Struktur- und Linkmerkmale prädiktiv für die wahrgenommene Seitenqualität sind. Dass zwei andere, unter MDI relevant erscheinende Merkmale sich bei genauerer Prüfung als wertlos erweisen (4.3), zeigt dagegen den eigentlichen methodischen Ertrag dieser Arbeit: Eine unreflektierte Feature-Importance-Analyse hätte hier in die Irre geführt. Die Dekorrelations-Analyse (4.5) präzisiert das Bild: Der Informationsgewinn der sechs Merkmale ist in dieser Stichprobe real, aber geringer als ihre Redundanz: Drei von sechs messen im Wesentlichen denselben „Umfang". Ein schlankeres Merkmalsset, also vier statt sechs Merkmale ohne die beiden redundanten Umfangs-Indikatoren, wäre der Ausgangspunkt für ähnliche Analysen, mit dem Vorbehalt aus 4.5, dass gerade diese Vier-Merkmale-Lösung die extremste Seite als Single-Page-Cluster isoliert. Die Empfehlung ist damit vorläufig, bis sie an einem größeren Seitenkorpus geprüft ist.

Das Profil von wiesbaden.de (4.4), schlank im Umfang, aber mit der tiefsten Verschachtelung, zeigt zudem, dass Komplexität kein eindimensionales Konstrukt ist. Butkiewicz et al. (2011) argumentieren in dieselbe Richtung und kombinieren mehrere unabhängige Metrikfamilien mit einem Außenkriterium, genau die Kombination, die hier zu grob geriet, um Strukturunterschiede aufzulösen. Dass ausgerechnet `link_count` als Einzelmetrik am tragfähigsten bleibt, fügt sich zu Chens (2018) Outdegree-Ansatz.

### 5.2 Grenzen und Verallgemeinerbarkeit

Die beiden Erfassungslücken aus 3.1 unterscheiden sich in der Ursache, nicht nur im Ergebnis, nämlich bei bpb.de ein Rendering-Problem (clientseitiges Nachladen), bei wiesbaden.de ein Scope-Problem (Formular außerhalb der gecrawlten Domain). Für die Praxis folgt daraus, dass ein Crawler-Tool dieser Art eine leere Merkmalsauszählung nicht kommentarlos als Nullwert ausgeben sollte, sondern die wahrscheinliche Ursache mit ausweisen müsste. Ob die gefundenen Cluster-Typen auf andere Websitegattungen (E-Commerce, Social Media) übertragbar sind, bleibt offen. Die modulare Architektur erlaubt aber die Erweiterung um weitere Merkmale ohne strukturellen Umbau.

### 5.3 Einschränkungen

**Externes Kriterium und Website-Konfundierung:** Das einzige geprüfte externe Kriterium (4.6) bestätigt weder Clusterzugehörigkeit noch die wichtigsten Merkmale und deckt nur einen Ausschnitt möglicher Außenkriterien ab (Accessibility und Nutzereinschätzung fehlen). Insbesondere die *wahrgenommene* Komplexität, die Tuch et al. (2012) und Miniukovich und De Angeli (2014) als eigenständige, verhaltensrelevante Dimension belegen, wurde nicht erhoben. Ob die strukturellen Merkmale abbilden, was Nutzende unter Komplexität verstehen, bleibt damit offen. Mit nur 3 Websites (47 Beobachtungen, die zu drei Websites gehören, statt unabhängig zu sein, ARI = 0,243) lässt sich zudem nicht sicher zwischen „generalisierbarem Seitentyp" und „individueller Website-Eigenheit" trennen.

**Stichprobenauswahl:** Ausgewählt wurden die drei Websites nach öffentlicher Zugänglichkeit und einer robots.txt ohne für die Crawling-Pfade einschlägige Disallow-Einträge. Das ist eine Positivselektion, die restriktiver geschützte, oft strukturell komplexere Websites systematisch ausschließt.
**Rechtlicher Rahmen:** Die robots.txt-Konformität (3.1) deckt nur die technische Zugriffsebene ab. Nutzungsbedingungen der jeweiligen Website können automatisiertes Crawling unabhängig davon einschränken. Für die hier gecrawlten drei öffentlichen Informations- und Verwaltungsportale wurden ausschließlich frei zugängliche, nicht personenbezogene Inhalte zu Forschungszwecken erfasst. Eine kommerzielle Nutzung der Rohdaten war nicht Gegenstand dieser Arbeit.

**Einzelner Zeitpunkt:** Die Analyse bildet einen Snapshot ab und erlaubt keine Aussage über zeitliche Entwicklung. Angesichts der von Ntoulas et al. (2004) gemessenen Dynamik des Webs, wonach sich ein erheblicher Teil der Seiten wöchentlich wesentlich verändert, ist das keine rein theoretische, sondern eine substanzielle Einschränkung.

---

## 6. Fazit

Die zentrale Forschungsfrage ist damit differenziert zu beantworten. Automatisierte Merkmalsextraktion und Clustering von Webseiten sind technisch machbar, ein belastbarer Mehrwert des mehrdimensionalen Modells gegenüber einer Einzelmetrik lässt sich mit dieser Stichprobe dagegen nicht zeigen. Auch die Dekorrelations-Analyse (4.5) verbessert das Mehrdimensionale nur auf die „gut"-Schwelle, ohne die Einzelmetrik-Baseline zu erreichen. Jede der in dieser Arbeit durchgeführten Robustheitsprüfungen deckt einen anderen Punkt auf, an dem eine oberflächliche Analyse zu falschen Schlüssen geführt hätte: die suboptimale Cluster-Anzahl, eine durch MDI verzerrte Merkmalsrangfolge, eine durch Einzel-Split überschätzte Modellgüte (stratifiziert 0,94 statt 1,00) und eine Einzelmetrik, die im internen Gütekriterium sogar besser abschneidet als das volle Sechs-Merkmale-Modell. Am schwersten wiegt der Befund aus 4.6, denn erst der Test gegen ein unabhängiges Kriterium zeigt, dass die gefundene Clusterstruktur im geprüften Außenkriterium ohne nachweisbaren Effekt bleibt.

Für die Praxis bedeutet dies, dass ein Werkzeug wie das hier entwickelte Websites strukturell beschreiben kann, aber ohne begleitende externe Validierung keine belastbare Aussage über praktische Relevanz trifft. Für die Methodik folgt daraus eine allgemeinere Lehre für vergleichbare Arbeiten: Cluster-Anzahl, Feature-Importance-Verfahren und Modellbewertung sollten grundsätzlich gegeneinander geprüft werden, bevor aus einem einzelnen Durchlauf Schlüsse gezogen werden. Die dabei durchlaufene Prüfabfolge (k-Scan, Einzelmetrik-Baseline, Dekorrelation, Permutations- statt MDI-Importance, stratifizierte Cross-Validation, externes Kriterium) ist als wiederverwendbare Checkliste für Clustering-Studien auf tabellarischen Merkmalen formulierbar. Ebenso ist die Pipeline aus Crawler, Ladern und Merkmalsberechnung unabhängig von dieser Datenlage wiederverwendbar.

---

## Daten- und Analyse-Verfügbarkeit

Crawl-Artefakte (`websites/`), Merkmalsdatei (`new_web_features.csv`) und Crawler (`mini_crawler.py`) sind Teil des versionskontrollierten Projekts. Die Merkmalsdatei entspricht exakt der Tool-Pipeline aus den Crawl-Artefakten , verifiziert über `website_loader` und `web_features`,. Alle Kennzahlen der Tabellen 1–5 sowie k-Scan, Baseline, Dekorrelation, Log-Transform-Variante, Feature-Importance, stratifizierte Cross-Validation, Bootstrap und Cluster-Stabilität erzeugt `check_web_analysis.py` aus der CSV, inklusive der Abbildung. Seed-abhängige Größen sind mit festen, dokumentierten Saaten versehen. **Nicht verfügbar sind die HTTP-Antwortzeit-Messungen hinter Tabelle 6 und Tabelle 7 (Abschnitt 4.6)**: Die Einzelmessungen wurden nicht archiviert. Die berichteten Werte sind als nicht reproduzierbar gekennzeichnet und sollten bei einer Replikation neu erhoben werden.

---

## Literatur

Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32.

Butkiewicz, M., Madhyastha, H. V., & Sekar, V. (2011). Understanding website complexity: Measurements, metrics, and implications. *Proceedings of the 11th ACM SIGCOMM Conference on Internet Measurement (IMC '11)*.

Chen, M. (2018). Improving website structure through reducing information overload. *Decision Support Systems, 110*, 84–94.

Hubert, L., & Arabie, P. (1985). Comparing partitions. *Journal of Classification, 2*(1), 193–218.

Ivory, M. Y., & Hearst, M. A. (2002). Statistical profiles of highly-rated web sites. *Proceedings of CHI 2002*, 367–374.

Miniukovich, A., & De Angeli, A. (2014). Quantification of interface visual complexity. *Proceedings of the 2014 International Working Conference on Advanced Visual Interfaces (AVI '14)*. ACM.

Ntoulas, A., Cho, J., & Olston, C. (2004). What's new on the web? The evolution of the web from a search engine perspective. *Proceedings of the 13th International Conference on World Wide Web (WWW '04)*.

Qi, X., & Davison, B. D. (2009). Web page classification: Features and algorithms. *ACM Computing Surveys, 41*(2), Artikel 12.

Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics, 20*, 53–65.

Tuch, A. N., Presslaber, E. E., Stöcklin, M., Opwis, K., & Bargas-Avila, J. A. (2012). The role of visual complexity and prototypicality regarding first impression of websites: Working towards understanding aesthetic judgments. *International Journal of Human–Computer Studies*.


---

## Ehrenwörtliche Erklärung

Hiermit erkläre ich ehrenwörtlich, dass ich die vorliegende Arbeit selbstständig und nur unter
Verwendung der angegebenen Hilfsmittel angefertigt habe. Die aus fremden Quellen direkt oder
indirekt übernommenen Gedanken sind als solche kenntlich gemacht. Die Arbeit wurde bisher in
gleicher oder ähnlicher Form keiner anderen Prüfungsbehörde vorgelegt und ist noch nicht
veröffentlicht.

Die Analyse- und Reproduktionsskripte wurden unter Zuhilfenahmen eines KI-gestützten
Programmierwerkzeugs (Claude Code) erstellt und geprüft. Die inhaltliche Konzeption, die
Datenauswertung und die Interpretation liegen bei mir. Die Arbeit wurde gemäß den Regeln
guter wissenschaftlicher Praxis erstellt.

**[ORT], den [DATUM]**

**[UNTERSCHRIFT]**

*(Unterschrift bei Abgabe in Dokument/PDF einfügen, diese Seite gehört zur Hausarbeit)*
