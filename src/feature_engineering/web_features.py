"""AP10 – Feature computation for crawled web pages and websites."""

from __future__ import annotations

import pandas as pd

from src.models.web_records import PageRecord, WebsiteRecord


def page_features(page: PageRecord) -> dict:
    """Compute a flat feature dict for one page."""
    dom_depth = _dom_depth(page.dom) if page.dom else 0
    dom_nodes = _dom_node_count(page.dom) if page.dom else 0

    return {
        "page_id":       page.page_id,
        "url":           page.url or "",
        "link_count":    page.link_count,
        "form_count":    page.form_count,
        "media_count":   page.media_count,
        "text_length":   page.text_length,
        "dom_depth":     dom_depth,
        "dom_nodes":     dom_nodes,
        "has_screenshot": int(page.has_screenshot),
    }


def website_features(website: WebsiteRecord) -> dict:
    """Compute aggregated features across all pages of one website."""
    if not website.pages:
        return {"website_id": website.website_id, "page_count": 0}

    page_dicts = [page_features(p) for p in website.pages]
    df = pd.DataFrame(page_dicts)

    numeric_cols = ["link_count", "form_count", "media_count", "text_length", "dom_depth", "dom_nodes"]
    agg: dict = {"website_id": website.website_id, "page_count": website.page_count}

    for col in numeric_cols:
        if col in df.columns:
            agg[f"{col}_mean"] = round(df[col].mean(), 2)
            agg[f"{col}_max"]  = int(df[col].max())
            agg[f"{col}_sum"]  = int(df[col].sum())

    return agg


def pages_to_dataframe(website: WebsiteRecord) -> pd.DataFrame:
    return pd.DataFrame([page_features(p) for p in website.pages])


def websites_to_dataframe(websites: list[WebsiteRecord]) -> pd.DataFrame:
    return pd.DataFrame([website_features(w) for w in websites])


# ── DOM helpers ───────────────────────────────────────────────────────────────

def _dom_depth(node, current: int = 0) -> int:
    if not isinstance(node, dict):
        return current
    children = node.get("children") or node.get("childNodes") or []
    dict_children = [c for c in children if isinstance(c, dict)]
    if not dict_children:
        return current
    return max(_dom_depth(child, current + 1) for child in dict_children)


def _dom_node_count(node) -> int:
    if not isinstance(node, dict):
        return 0
    children = node.get("children") or node.get("childNodes") or []
    return 1 + sum(_dom_node_count(c) for c in children if isinstance(c, dict))
