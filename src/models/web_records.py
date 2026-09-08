"""Data models for crawled websites and pages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PageRecord:
    """
    One crawled sub-page.

    All structured JSON artefacts are loaded into typed fields.
    Missing files stay None so callers can check availability explicitly.
    """

    page_id: str                             # folder name, e.g. "1", "2"
    source_dir: str                          # absolute path to page folder
    url: str | None = None

    # Structured artefacts (None = file not present)
    visible_text: dict[str, Any] | None = None
    links: list[dict[str, Any]] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    media: list[dict[str, Any]] = field(default_factory=list)
    dom: dict[str, Any] | None = None

    screenshot_path: str | None = None      # absolute path to screenshot.png
    raw_html_path: str | None = None        # absolute path to raw.html / raw_html.json
    load_errors: dict[str, str] = field(default_factory=dict)  # Artefakt → Fehlerursache (korrupt statt still 0)

    meta: dict[str, Any] = field(default_factory=dict)

    # ── Derived convenience properties ───────────────────────────────────────

    @property
    def link_count(self) -> int:
        return len(self.links)

    @property
    def form_count(self) -> int:
        return len(self.forms)

    @property
    def media_count(self) -> int:
        return len(self.media)

    @property
    def has_screenshot(self) -> bool:
        return self.screenshot_path is not None

    @property
    def text_length(self) -> int:
        if self.visible_text is None:
            return 0
        text = self.visible_text.get("text") or self.visible_text.get("content") or ""
        return len(str(text))


@dataclass
class WebsiteRecord:
    """
    One crawled website consisting of multiple pages plus shared metadata.
    """

    website_id: str                          # folder name, e.g. "1"
    source_dir: str                          # absolute path to website folder
    pages: list[PageRecord] = field(default_factory=list)

    portal_meta: dict[str, Any] | None = None
    asset_index: dict[str, Any] | None = None
    shared_assets_dir: str | None = None

    meta: dict[str, Any] = field(default_factory=dict)

    # ── Derived convenience properties ───────────────────────────────────────

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def total_links(self) -> int:
        return sum(p.link_count for p in self.pages)

    @property
    def total_media(self) -> int:
        return sum(p.media_count for p in self.pages)

    def get_page(self, page_id: str) -> PageRecord | None:
        return next((p for p in self.pages if p.page_id == page_id), None)
