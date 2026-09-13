"""AP10 – Konsistenzanalyse gecrawlter Seiten (Screenshots ↔ JSON-Merkmale).

Prüft pro Seite, ob die vorliegenden Artefakte zueinander passen:

  * Screenshot vorhanden/lesbar/nicht leer (PIL-Bildstatistik)
  * strukturierte JSONs vorhanden (Text, DOM)
  * Widersprüche: Inhalt laut JSON, aber (nahezu) leerer Screenshot;
    Screenshot vorhanden, aber keine Strukturdaten; raw.html ohne dom.json
    (und umgekehrt)

Ergebnis: lange Tabelle (eine Zeile je Seite und Befund) plus zusammen-
fassende Zählung je Website.
"""

from __future__ import annotations

import pandas as pd

from src.models.web_records import PageRecord, WebsiteRecord

# Ein Screenshot gilt als "nahezu leer", wenn die Grauwert-Standard-
# abweichung darunter liegt (einfarbige/fehlerhafte Aufnahmen).
_BLANK_STD_THRESHOLD = 3.0


def _screenshot_stats(path: str | None) -> dict:
    """Bildstatistik des Screenshots: vorhanden, Auflösung, Std-Abweichung."""
    if path is None:
        return {"screenshot": False}
    try:
        from PIL import Image
        with Image.open(path) as img:
            gray = img.convert("L")
            small = gray.resize((64, 64))
            pixels = list(small.getdata())
            n = len(pixels)
            mean = sum(pixels) / n
            std = (sum((p - mean) ** 2 for p in pixels) / n) ** 0.5
            return {"screenshot": True, "width": img.width, "height": img.height,
                    "gray_std": round(std, 2)}
    except Exception:
        return {"screenshot": False, "screenshot_unlesbar": True}


def analyze_page_consistency(page: PageRecord) -> dict:
    """Konsistenz-Befunde für eine Seite (leere issues-Liste = konsistent)."""
    stats = _screenshot_stats(page.screenshot_path)
    text_len = page.text_length
    has_dom = page.dom is not None
    has_raw = page.raw_html_path is not None

    issues: list[str] = []
    if not stats.get("screenshot"):
        if stats.get("screenshot_unlesbar"):
            issues.append("Screenshot vorhanden, aber nicht lesbar")
        elif text_len > 0 or has_dom:
            issues.append("Kein Screenshot, obwohl JSON-Inhalte vorliegen")
    elif stats.get("gray_std", 0.0) < _BLANK_STD_THRESHOLD:
        if text_len > 500:
            issues.append(
                f"Screenshot nahezu leer (σ={stats.get('gray_std')}), "
                f"aber text_length={text_len}"
            )
        else:
            issues.append(f"Screenshot nahezu leer (σ={stats.get('gray_std')})")

    if text_len == 0 and (has_dom or stats.get("screenshot")):
        issues.append("Kein sichtbarer Text, obwohl DOM/Screenshot vorliegen")
    if has_raw and not has_dom:
        issues.append("raw.html vorhanden, aber dom.json fehlt")
    if has_dom and not has_raw:
        issues.append("dom.json vorhanden, aber raw.html fehlt")

    return {
        "page_id": page.page_id,
        "url": page.url or "",
        **stats,
        "text_length": text_len,
        "dom_nodes": len(page.dom.get("children", [])) if isinstance(page.dom, dict) else 0,
        "issues": "; ".join(issues),
        "n_issues": len(issues),
    }


def website_consistency(website: WebsiteRecord) -> pd.DataFrame:
    """Konsistenztabelle aller Seiten einer Website."""
    return pd.DataFrame([analyze_page_consistency(p) for p in website.pages])


def consistency_summary(df: pd.DataFrame) -> dict:
    """Zusammenfassung: Seiten mit/ohne Screenshot, auffällige Seiten."""
    if df.empty:
        return {"pages": 0}
    return {
        "pages": int(len(df)),
        "mit_screenshot": int(df["screenshot"].sum()) if "screenshot" in df else 0,
        "auffällige_seiten": int((df["n_issues"] > 0).sum()),
        "befunde": int(df["n_issues"].sum()),
    }
