"""
Zieht Screenshots für bestehende Website-Crawls nach, OHNE die analytischen
JSON-Artefakte (links/dom/visible_text/...) zu verändern — die bleiben
unverändert die Grundlage der Paper-Kennzahlen.

Nutzung:
    python backfill_screenshots.py <website_hauptordner>   # alle Websites
    python backfill_screenshots.py <ein_website_ordner>    # eine Website

Liest die URL je Seite aus visible_text.json; Seiten mit vorhandenem
screenshot.png werden übersprungen. Benötigt playwright + chromium.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from mini_crawler import ScreenshotTaker


def _page_urls(website_dir: Path) -> list[tuple[Path, str]]:
    """(Seitenordner, URL) für alle Seiten mit bekannter URL."""
    out: list[tuple[Path, str]] = []
    pages_dir = website_dir / "pages"
    if not pages_dir.is_dir():
        return out
    for page_dir in sorted(pages_dir.iterdir(), key=lambda p: p.name):
        if not page_dir.is_dir() or (page_dir / "screenshot.png").exists():
            continue
        vt_file = page_dir / "visible_text.json"
        if not vt_file.is_file():
            continue
        try:
            url = (json.loads(vt_file.read_text(encoding="utf-8")) or {}).get("url")
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            url = None
        if url:
            out.append((page_dir, url))
    return out


def backfill(root: Path, delay: float = 1.0) -> int:
    targets = [(website, _page_urls(website)) for website in
               ([root] if (root / "pages").is_dir() else sorted(
                   w for w in root.iterdir() if w.is_dir() and (w / "pages").is_dir()))]
    todo = [(page, url) for _, pages in targets for page, url in pages]
    total = sum(len(pages) for _, pages in targets)
    print(f"Seiten ohne Screenshot: {len(todo)} (von {total} Seiten insgesamt)")
    if not todo:
        return 0

    shooter = ScreenshotTaker()
    if not shooter.start():
        return 1
    done = 0
    try:
        for page_dir, url in todo:
            if shooter.take(url, page_dir / "screenshot.png"):
                done += 1
                print(f"  OK  {page_dir.parent.name}/{page_dir.name}  {url}")
            time.sleep(delay)
    finally:
        shooter.stop()
    print(f"\nFertig: {done}/{len(todo)} Screenshots erzeugt.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Nutzung: python backfill_screenshots.py <ordner>")
        sys.exit(1)
    sys.exit(backfill(Path(sys.argv[1])))
