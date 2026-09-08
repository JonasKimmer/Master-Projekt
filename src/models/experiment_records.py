"""Data models for multimodal experiment trials."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    TASK_START = "task_start"
    TASK_END = "task_end"
    BASELINE_START = "baseline_start"
    BASELINE_END = "baseline_end"
    QUESTIONNAIRE_START = "questionnaire_start"
    QUESTIONNAIRE_END = "questionnaire_end"
    UNKNOWN = "unknown"


@dataclass
class EventRecord:
    """A single timestamped event within a trial."""

    timestamp: float          # Unix ms or relative ms – whichever the file uses
    event_type: EventType
    label: str                # Raw label string from the source file
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SensorStreamRecord:
    """
    One sensor modality for a trial.

    channels holds one key per signal channel, e.g.:
      {"heart_rate": [...], "gsr": [...], "gaze_x": [...], "gaze_y": [...]}

    timestamps is a parallel list of float values (same length as each channel).

    New sources (OpenBCI, IMU, …) add entries to channels without touching
    the surrounding model.
    """

    source: str                              # e.g. "fusion_merged", "openbci"
    modality: str                            # e.g. "eye_tracking", "ppg", "eeg"
    timestamps: list[float] = field(default_factory=list)
    channels: dict[str, list[Any]] = field(default_factory=dict)
    sampling_rate_hz: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrialRecord:
    """One experiment trial with its events and sensor streams."""

    trial_id: str
    source_dir: str                          # absolute path to the trial folder
    events: list[EventRecord] = field(default_factory=list)
    streams: list[SensorStreamRecord] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def get_stream(self, modality: str) -> SensorStreamRecord | None:
        """Return the first stream matching the given modality, or None."""
        return next((s for s in self.streams if s.modality == modality), None)


@dataclass
class Segment:
    """A time segment derived from a paired start/end event."""

    label: str                               # base label, e.g. "task_1", "baseline"
    segment_type: str                        # "task" | "baseline" | "questionnaire" | "unknown"
    start_ms: float
    end_ms: float | None                     # None if end event is missing
    start_event: EventRecord
    end_event: EventRecord | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.end_ms is None:
            return None
        return self.end_ms - self.start_ms

    @property
    def is_complete(self) -> bool:
        return self.end_ms is not None


@dataclass
class TrialTimeline:
    """Ordered sequence of segments for one trial, with quality annotations."""

    trial_id: str
    segments: list[Segment] = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)

    @property
    def has_missing_ends(self) -> bool:
        return any(not s.is_complete for s in self.segments)

    def get_segments_by_type(self, segment_type: str) -> list[Segment]:
        return [s for s in self.segments if s.segment_type == segment_type]


@dataclass
class WindowDefinition:
    """
    Configuration for a time window over sensor data.

    mode:
      "fixed"   – absolute start/end in ms
      "sliding" – step-based sweep across the full stream
      "task"    – anchored to a specific task label from EventRecord
    """

    window_id: str
    mode: str                                # "fixed" | "sliding" | "task"
    duration_ms: float
    step_ms: float | None = None            # sliding only
    task_label: str | None = None           # task mode only
    offset_start_ms: float = 0.0           # shift relative to anchor
    offset_end_ms: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class WindowFeatureRecord:
    """Aggregated features computed for one window instance."""

    window_id: str
    trial_id: str
    modality: str
    start_ms: float
    end_ms: float
    # channel_name → {"mean": …, "std": …, "min": …, "max": …, …}
    features: dict[str, dict[str, float]] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
