"""AP8 – Quality checks for multimodal sensor streams."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.experiment_records import SensorStreamRecord, TrialRecord

# ── Plausibility ranges per channel keyword ───────────────────────────────────
# (min_valid, max_valid)
_PLAUSIBILITY: dict[str, tuple[float, float]] = {
    "heart_rate":       (30.0,  220.0),
    "hr":               (30.0,  220.0),
    "ppgmv":            (0.0,   4096.0),  # raw mV from Shimmer PPG ADC
    "gsrconductanceus": (0.0,   100.0),   # µS  (microsiemens)
    "gsrkohm":          (0.01,  5000000.0),  # kΩ skin resistance – very wide range
    "eda":              (0.0,   100.0),
    "gaze_x":           (-0.2,  1.2),     # normalised 0–1, allow slight overshoot
    "gaze_y":           (-0.2,  1.2),
    # Neurons fused streams name the channels LeftX/RightX/LeftY/RightY;
    # matching runs on the lowercased, separator-stripped channel name
    # ("gaze.LeftX" → "gazeleftx"), so these keys must be substring-exact.
    "leftx":            (-0.2,  1.2),
    "rightx":           (-0.2,  1.2),
    "lefty":            (-0.2,  1.2),
    "righty":           (-0.2,  1.2),
    "pupil":            (1.0,   10.0),    # mm realistic pupil diameter
    "temperature":      (20.0,  45.0),    # °C skin
}


@dataclass
class ChannelQuality:
    channel: str
    n_samples: int
    n_missing: int
    n_duplicates: int
    n_out_of_range: int
    max_gap_ms: float
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0


@dataclass
class StreamQualityReport:
    trial_id: str
    source: str
    modality: str
    n_timestamps: int
    duplicate_timestamps: int
    max_gap_ms: float
    channels: list[ChannelQuality] = field(default_factory=list)
    global_issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.global_issues and all(c.ok for c in self.channels)

    def summary(self) -> str:
        if self.ok:
            return f"[{self.trial_id}/{self.source}] OK"
        issues = self.global_issues + [i for c in self.channels for i in c.issues]
        return f"[{self.trial_id}/{self.source}] {len(issues)} issue(s): " + "; ".join(issues[:3])


def check_stream(trial_id: str, stream: SensorStreamRecord, gap_threshold_ms: float = 3000.0) -> StreamQualityReport:
    ts = stream.timestamps
    report = StreamQualityReport(
        trial_id=trial_id,
        source=stream.source,
        modality=stream.modality,
        n_timestamps=len(ts),
        duplicate_timestamps=0,
        max_gap_ms=0.0,
    )

    if not ts:
        report.global_issues.append("Stream is empty")
        return report

    # Duplicate timestamps
    dup_count = len(ts) - len(set(ts))
    report.duplicate_timestamps = dup_count
    if dup_count > 0:
        report.global_issues.append(f"{dup_count} duplicate timestamp(s)")

    # Sampling gaps
    sorted_ts = sorted(ts)
    gaps = [sorted_ts[i + 1] - sorted_ts[i] for i in range(len(sorted_ts) - 1)]
    if gaps:
        max_gap = max(gaps)
        report.max_gap_ms = max_gap
        if max_gap > gap_threshold_ms:
            report.global_issues.append(f"Max sampling gap {max_gap:.0f} ms (threshold {gap_threshold_ms:.0f} ms)")

    # Per-channel checks
    for ch_name, values in stream.channels.items():
        ch_issues: list[str] = []
        n_missing = sum(1 for v in values if v is None)
        n_out = 0

        ch_lower = ch_name.lower().replace(".", "").replace("_", "")
        plausible_key = next((k for k in _PLAUSIBILITY if k.replace("_", "") in ch_lower), None)
        if plausible_key:
            lo, hi = _PLAUSIBILITY[plausible_key]
            n_out = sum(1 for v in values if v is not None and not (lo <= float(v) <= hi))
            if n_out > 0:
                ch_issues.append(f"{n_out} value(s) outside plausible range [{lo}, {hi}]")

        if n_missing > 0:
            ch_issues.append(f"{n_missing} missing value(s)")

        # Channel outage: long consecutive identical values
        # Skip binary channels (only 0/1) – validity flags are expected to be constant
        unique_vals = set(str(v) for v in values if v is not None)
        is_binary = unique_vals <= {"0", "1", "0.0", "1.0"}
        if not is_binary:
            streak = 1
            max_streak = 1
            for i in range(1, len(values)):
                if values[i] == values[i - 1]:
                    streak += 1
                    max_streak = max(max_streak, streak)
                else:
                    streak = 1
            # Only flag if streak covers >5% of total samples and is at least 50 samples
            # (avoids false positives from sensor fusion at mismatched rates)
            outage_threshold = max(50, int(len(values) * 0.05))
            if max_streak >= outage_threshold:
                ch_issues.append(f"Constant-value streak of {max_streak} samples (possible outage)")

        # Duplicate count within channel (timestamps already checked globally)
        n_dups = len(values) - len(set(str(v) for v in values))

        report.channels.append(ChannelQuality(
            channel=ch_name,
            n_samples=len(values),
            n_missing=n_missing,
            n_duplicates=n_dups,
            n_out_of_range=n_out,
            max_gap_ms=report.max_gap_ms,
            issues=ch_issues,
        ))

    return report


def check_trial(trial: TrialRecord, gap_threshold_ms: float = 3000.0) -> list[StreamQualityReport]:
    return [check_stream(trial.trial_id, s, gap_threshold_ms) for s in trial.streams]
