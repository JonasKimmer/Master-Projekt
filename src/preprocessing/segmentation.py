"""Task and segment logic for experiment trials.

Takes a list of EventRecord objects and produces a TrialTimeline with
paired Segment objects. Handles missing end events gracefully.
"""

from __future__ import annotations

import re
from collections import defaultdict

from src.models.experiment_records import (
    EventRecord,
    EventType,
    Segment,
    TrialRecord,
    TrialTimeline,
)

# ── Label helpers ─────────────────────────────────────────────────────────────

_START_TYPES = {EventType.TASK_START, EventType.BASELINE_START, EventType.QUESTIONNAIRE_START}
_END_TYPES   = {EventType.TASK_END,   EventType.BASELINE_END,   EventType.QUESTIONNAIRE_END}

_START_SUFFIXES = ("_start", "_begin", " start", " begin")
_END_SUFFIXES   = ("_end",   "_stop",  " end",   " stop")

_TYPE_MAP: dict[EventType, str] = {
    EventType.TASK_START:          "task",
    EventType.TASK_END:            "task",
    EventType.BASELINE_START:      "baseline",
    EventType.BASELINE_END:        "baseline",
    EventType.QUESTIONNAIRE_START: "questionnaire",
    EventType.QUESTIONNAIRE_END:   "questionnaire",
}


def _base_label(label: str) -> str:
    """Strip start/end suffix to get a matchable base label."""
    lower = label.lower()
    for suffix in _START_SUFFIXES + _END_SUFFIXES:
        if lower.endswith(suffix):
            return label[: len(label) - len(suffix)].strip("_-: ").strip()
    # Fallback: also handles colon-separated "task:start" → "task"
    return re.sub(r"[\s_:-]*(start|end|begin|stop)[\s_:-]*$", "", lower, flags=re.I).strip()


def _segment_type(event_type: EventType) -> str:
    return _TYPE_MAP.get(event_type, "unknown")


# ── Core segmentation ─────────────────────────────────────────────────────────

def build_timeline(trial_id: str, events: list[EventRecord]) -> TrialTimeline:
    """
    Pair start/end events into Segment objects.

    Strategy:
    - Group events by base_label.
    - Within each group, match the first unmatched START to the next END.
    - Unmatched STARTs produce incomplete segments (end_ms=None).
    - Orphaned END events (no preceding START) are recorded as quality issues.
    """
    timeline = TrialTimeline(trial_id=trial_id)
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    # pending_starts[base_label] = queue of unmatched start events.
    # Matching-Regeln pro END-Event (robust gegenüber asymmetrischen
    # Domain-Metadaten, ohne Cross-Domain-Fehlpaarungen zu erlauben):
    #   1. ältester Start mit exakt passender Domain
    #   2. ältester Start ohne Domain-Info
    #   3. nur wenn das END selbst keine Domain trägt: ältester Start
    #      insgesamt (Domain ist dann nicht unterscheidbar)
    pending_starts: dict[str, list[EventRecord]] = defaultdict(list)

    def _find_match(queue: list[EventRecord], end_domain) -> int | None:
        for i, s in enumerate(queue):
            if s.meta.get("domain") == end_domain:
                return i
        for i, s in enumerate(queue):
            if s.meta.get("domain") is None:
                return i
        if end_domain is None and queue:
            return 0
        return None

    for event in sorted_events:
        base = _base_label(event.label)
        seg_type = _segment_type(event.event_type)

        if event.event_type in _START_TYPES:
            pending_starts[base].append(event)

        elif event.event_type in _END_TYPES:
            match_idx = _find_match(pending_starts[base], event.meta.get("domain"))
            if match_idx is not None:
                start_event = pending_starts[base].pop(match_idx)
                timeline.segments.append(Segment(
                    label=base,
                    segment_type=seg_type,
                    start_ms=start_event.timestamp,
                    end_ms=event.timestamp,
                    start_event=start_event,
                    end_event=event,
                    # Domain bevorzugt vom Start-Event, sonst vom End-Event
                    domain=(start_event.meta.get("domain") or event.meta.get("domain")),
                ))
            else:
                timeline.quality_issues.append(
                    f"Orphaned END event at t={event.timestamp:.0f} ms (label='{event.label}') — no matching START"
                )

    # Flush unmatched STARTs as incomplete segments
    for base, stack in pending_starts.items():
        for start_event in stack:
            seg_type = _segment_type(start_event.event_type)
            timeline.segments.append(Segment(
                label=base,
                segment_type=seg_type,
                start_ms=start_event.timestamp,
                end_ms=None,
                start_event=start_event,
                end_event=None,
                domain=start_event.meta.get("domain"),
            ))
            timeline.quality_issues.append(
                f"Missing END for segment '{base}' started at t={start_event.timestamp:.0f} ms"
            )

    # Sort final segments by start time
    timeline.segments.sort(key=lambda s: s.start_ms)

    # Check for overlapping segments
    for i in range(len(timeline.segments) - 1):
        a, b = timeline.segments[i], timeline.segments[i + 1]
        if a.end_ms is not None and b.start_ms < a.end_ms:
            timeline.quality_issues.append(
                f"Overlap: '{a.label}' (ends {a.end_ms:.0f} ms) overlaps '{b.label}' (starts {b.start_ms:.0f} ms)"
            )

    return timeline


def build_timeline_from_trial(trial: TrialRecord) -> TrialTimeline:
    """Convenience wrapper: build a TrialTimeline directly from a TrialRecord."""
    return build_timeline(trial.trial_id, trial.events)
