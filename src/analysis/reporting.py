"""AP12 – Export and reporting functions."""

from __future__ import annotations

import io
import json

import pandas as pd

from src.models.experiment_records import TrialTimeline, WindowFeatureRecord
from src.models.web_records import WebsiteRecord
from src.feature_engineering.web_features import pages_to_dataframe, websites_to_dataframe
from src.preprocessing.quality_checks import StreamQualityReport


# ── Trial / Segment exports ───────────────────────────────────────────────────

def timeline_to_dataframe(timeline: TrialTimeline) -> pd.DataFrame:
    rows = []
    for seg in timeline.segments:
        rows.append({
            "trial_id":     timeline.trial_id,
            "label":        seg.label,
            "type":         seg.segment_type,
            "start_ms":     seg.start_ms,
            "end_ms":       seg.end_ms,
            "duration_ms":  seg.duration_ms,
            "complete":     seg.is_complete,
        })
    return pd.DataFrame(rows)


def window_features_to_dataframe(records: list[WindowFeatureRecord]) -> pd.DataFrame:
    rows = []
    for r in records:
        base = {
            "window_id": r.window_id,
            "trial_id":  r.trial_id,
            "modality":  r.modality,
            "start_ms":  r.start_ms,
            "end_ms":    r.end_ms,
        }
        for ch, feats in r.features.items():
            for feat_name, val in feats.items():
                base[f"{ch}_{feat_name}"] = val
        rows.append(base)
    return pd.DataFrame(rows)


def quality_reports_to_dataframe(reports: list[StreamQualityReport]) -> pd.DataFrame:
    rows = []
    for r in reports:
        rows.append({
            "trial_id":            r.trial_id,
            "source":              r.source,
            "modality":            r.modality,
            "n_timestamps":        r.n_timestamps,
            "duplicate_timestamps": r.duplicate_timestamps,
            "max_gap_ms":          r.max_gap_ms,
            "ok":                  r.ok,
            "issues":              "; ".join(r.global_issues),
        })
    return pd.DataFrame(rows)


# ── Markdown report generators ────────────────────────────────────────────────

def trial_markdown_report(timeline: TrialTimeline) -> str:
    md = f"# Trial Report: {timeline.trial_id}\n\n"
    md += f"**Segments:** {len(timeline.segments)}  \n"
    md += f"**Complete segments:** {sum(s.is_complete for s in timeline.segments)}  \n"
    md += f"**Quality issues:** {len(timeline.quality_issues)}\n\n"

    if timeline.quality_issues:
        md += "## Quality Issues\n"
        for issue in timeline.quality_issues:
            md += f"- {issue}\n"
        md += "\n"

    md += "## Segments\n\n"
    df = timeline_to_dataframe(timeline)
    if not df.empty:
        for col in ("start_ms", "end_ms", "duration_ms"):
            if col in df.columns:
                df[col] = df[col].apply(lambda x: int(x) if x is not None and str(x) != "nan" else "")
        md += df.to_markdown(index=False) + "\n"
    return md


def website_markdown_report(website: WebsiteRecord) -> str:
    md = f"# Website Report: {website.website_id}\n\n"
    md += f"**Pages:** {website.page_count}  \n"
    md += f"**Total links:** {website.total_links}  \n"
    md += f"**Total media:** {website.total_media}\n\n"
    md += "## Page Overview\n\n"
    df = pages_to_dataframe(website)
    if not df.empty:
        md += df.to_markdown(index=False) + "\n"
    return md


# ── Byte-stream helpers for Streamlit download buttons ────────────────────────

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def str_to_bytes(text: str) -> bytes:
    return text.encode("utf-8")
