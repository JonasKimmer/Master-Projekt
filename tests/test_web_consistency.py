"""AP10: Konsistenzanalyse Screenshots <-> JSON-Merkmale."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.analysis.web_consistency import (
    analyze_page_consistency,
    consistency_summary,
    website_consistency,
)
from src.models.web_records import PageRecord, WebsiteRecord


def _page(page_id, *, screenshot=None, text="", dom=True, raw=True):
    return PageRecord(
        page_id=str(page_id), source_dir=f"/x/{page_id}", url=f"https://x/{page_id}",
        visible_text={"url": f"https://x/{page_id}", "text": text},
        links=[], forms=[], media=[],
        dom={"tag": "html", "children": [{"tag": "body"}]} if dom else None,
        screenshot_path=screenshot,
        raw_html_path=f"/x/{page_id}/raw.html" if raw else None,
    )


def _write_png(path: Path, blank: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    color = 255 if blank else None
    img = Image.new("RGB", (64, 64), color) if blank else \
        Image.frombytes("RGB", (64, 64), bytes((i * 7 % 256 for i in range(64 * 64 * 3))))
    img.save(path)
    return str(path)


class TestPageConsistency:
    def test_consistent_page_no_issues(self, tmp_path):
        shot = _write_png(tmp_path / "1" / "s.png", blank=False)
        p = _page(1, screenshot=shot, text="viel Inhalt " * 200)
        r = analyze_page_consistency(p)
        assert r["n_issues"] == 0 and r["screenshot"] is True

    def test_content_without_screenshot_flagged(self):
        p = _page(1, text="Inhalt " * 100)
        r = analyze_page_consistency(p)
        assert any("Kein Screenshot" in i for i in [r["issues"]])

    def test_blank_screenshot_with_text_flagged(self, tmp_path):
        shot = _write_png(tmp_path / "2" / "s.png", blank=True)
        p = _page(2, screenshot=shot, text="sehr viel Text " * 200)
        r = analyze_page_consistency(p)
        assert "nahezu leer" in r["issues"] and "text_length" in r["issues"]

    def test_raw_dom_mismatch_flagged(self, tmp_path):
        shot = _write_png(tmp_path / "3" / "s.png", blank=False)
        p = _page(3, screenshot=shot, text="x " * 100, dom=False)
        r = analyze_page_consistency(p)
        assert "dom.json fehlt" in r["issues"]

    def test_unreadable_screenshot_flagged(self, tmp_path):
        bad = tmp_path / "4" / "s.png"
        bad.parent.mkdir(parents=True)
        bad.write_text("kein bild", encoding="utf-8")
        p = _page(4, screenshot=str(bad), text="x " * 100)
        r = analyze_page_consistency(p)
        assert "nicht lesbar" in r["issues"]


class TestWebsiteConsistency:
    def test_summary_and_dataframe(self, tmp_path):
        shot = _write_png(tmp_path / "ok" / "s.png", blank=False)
        pages = [
            _page(1, screenshot=shot, text="Inhalt " * 100),
            _page(2, text="Inhalt " * 100),          # kein Screenshot
        ]
        w = WebsiteRecord(website_id="W", source_dir="/w", pages=pages)
        df = website_consistency(w)
        assert list(df["page_id"]) == ["1", "2"]
        s = consistency_summary(df)
        assert s == {"pages": 2, "mit_screenshot": 1, "auffällige_seiten": 1, "befunde": 1}
