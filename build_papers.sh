#!/bin/bash
# Baut die beiden Hausarbeits-Papers als DOCX (Inhaltsverzeichnis inkl.)
# und als druckfertiges HTML (Browser → Drucken → Als PDF speichern).
#
# Nutzung:  ./build_papers.sh     (oder: bash build_papers.sh)
# Ausgabe:  build/paper_1_kognitive_last.docx|.html
#           build/paper_2_webkomplexitaet.docx|.html
#
# Vor der Abgabe im DOCX/PDF noch erledigen (steht als [BITTE ...] im Text):
#   - Titelseite: Hochschule, Studiengang, Matrikelnummer, Betreuer:in, Datum
#   - Ehrenwörtliche Erklärung: Ort/Datum/Unterschrift
#   - Abbildungs-/Tabellenverzeichnis, falls von der Hochschule gefordert

set -e
cd "$(dirname "$0")"
mkdir -p build

for md in paper_1_kognitive_last paper_2_webkomplexitaet; do
    echo "→ $md"
    # DOCX: öffnet in Word/Pages; TOC wird als Feld eingefügt
    # (in Word ggf. Rechtsklick → Felder aktualisieren)
    pandoc "$md.md" \
        --toc --toc-depth=2 \
        --metadata lang=de \
        -o "build/$md.docx"

    # HTML: Druck-Layout, öffnen und „Als PDF drucken"
    pandoc "$md.md" \
        --toc --toc-depth=2 \
        --metadata lang=de \
        --standalone --embed-resources \
        -c build_papers.css \
        -o "build/$md.html"
done

echo "Fertig: $(ls build/ | tr '\n' ' ')"
