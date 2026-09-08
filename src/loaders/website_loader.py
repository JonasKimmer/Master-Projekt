"""Loader for crawled website folders.

Expected folder layout:
  <website_dir>/
    portal_meta.json
    asset_index.json
    shared_assets/
    pages/
      1/
        raw.html  (or raw_html.json)
        screenshot.png
        visible_text.json
        media.json
        links.json
        forms.json
        dom.json
      2/
        ...
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.loaders.sort_utils import natural_sort_key
from src.models.web_records import PageRecord, WebsiteRecord


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_json_safe(path: Path, errors: dict[str, str] | None = None) -> Any | None:
    """Return parsed JSON or None if file absent.

    Bei vorhandenem, aber unlesbarem/korruptem File wird None geliefert
    UND — wenn ein errors-Dict übergeben wird — der Artefaktname mit der
    Fehlerursache vermerkt. Ein korruptes Artefakt darf nicht still als
    'nicht gecrawlt' (Nullwert) durchgehen (s. Paper 2, 5.2).
    """
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as ex:
        if errors is not None:
            errors[path.name] = f"{type(ex).__name__}: {ex}"
        return None


def _find_raw_html(page_dir: Path) -> str | None:
    for name in ("raw.html", "raw_html.json"):
        candidate = page_dir / name
        if candidate.exists():
            return str(candidate.resolve())
    return None


# ── Page loader ───────────────────────────────────────────────────────────────

def _load_page(page_dir: Path) -> PageRecord:
    page_id = page_dir.name

    load_errors: dict[str, str] = {}
    visible_text = _load_json_safe(page_dir / "visible_text.json", load_errors)
    links_raw    = _load_json_safe(page_dir / "links.json", load_errors)
    forms_raw    = _load_json_safe(page_dir / "forms.json", load_errors)
    media_raw    = _load_json_safe(page_dir / "media.json", load_errors)
    dom          = _load_json_safe(page_dir / "dom.json", load_errors)

    # Normalise: ensure lists even if the file holds a dict wrapper
    def _to_list(val: Any) -> list[dict[str, Any]]:
        if val is None:
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, dict):
            # Some crawlers wrap the list under a key
            for v in val.values():
                if isinstance(v, list):
                    return v
            return [val]
        return []

    screenshot = page_dir / "screenshot.png"

    # Try to extract URL from visible_text or dom meta
    url: str | None = None
    if isinstance(visible_text, dict):
        url = visible_text.get("url") or visible_text.get("page_url")
    if url is None and isinstance(dom, dict):
        url = dom.get("url") or dom.get("page_url")

    return PageRecord(
        page_id=page_id,
        source_dir=str(page_dir.resolve()),
        url=url,
        visible_text=visible_text if isinstance(visible_text, dict) else None,
        links=_to_list(links_raw),
        forms=_to_list(forms_raw),
        media=_to_list(media_raw),
        dom=dom if isinstance(dom, dict) else None,
        screenshot_path=str(screenshot.resolve()) if screenshot.exists() else None,
        raw_html_path=_find_raw_html(page_dir),
        load_errors=load_errors,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def load_website(website_dir: str) -> WebsiteRecord:
    """Load a single website folder into a WebsiteRecord."""
    p = Path(website_dir)
    website_id = p.name

    portal_meta = _load_json_safe(p / "portal_meta.json")
    asset_index = _load_json_safe(p / "asset_index.json")

    shared_assets_dir = p / "shared_assets"
    shared_assets_path = str(shared_assets_dir.resolve()) if shared_assets_dir.exists() else None

    pages: list[PageRecord] = []
    pages_dir = p / "pages"
    if pages_dir.exists():
        for entry in sorted(pages_dir.iterdir(), key=lambda e: natural_sort_key(e.name)):
            if entry.is_dir():
                pages.append(_load_page(entry))

    return WebsiteRecord(
        website_id=website_id,
        source_dir=str(p.resolve()),
        pages=pages,
        portal_meta=portal_meta if isinstance(portal_meta, dict) else None,
        asset_index=asset_index if isinstance(asset_index, dict) else None,
        shared_assets_dir=shared_assets_path,
    )


def load_websites_from_dir(parent_dir: str) -> list[WebsiteRecord]:
    """Scan parent_dir and load each sub-folder that contains a pages/ directory."""
    p = Path(parent_dir)
    websites: list[WebsiteRecord] = []

    for entry in sorted(p.iterdir(), key=lambda e: natural_sort_key(e.name)):
        if entry.is_dir() and (entry / "pages").exists():
            websites.append(load_website(str(entry)))

    return websites
