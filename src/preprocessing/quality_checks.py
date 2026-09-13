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
    # Neurons fused streams name the channels LeftX/RightX/LeftY/RightY.
    # Matching ist EXAKT auf dem normalisierten Punkt-Segment des Kanal-
    # namens ("gaze.LeftX" → Segment "leftx"), siehe
    # _plausibility_for_channel — nicht per Substring über den Gesamtnamen.
    "leftx":            (-0.2,  1.2),
    "rightx":           (-0.2,  1.2),
    "lefty":            (-0.2,  1.2),
    "righty":           (-0.2,  1.2),
    "pupil":            (1.0,   10.0),    # mm realistic pupil diameter
    "temperature":      (20.0,  45.0),    # °C skin
    # IMU (Shimmer3, Kanäle shimmer.AccX/AccWrX/GyroX/MagX …).
    # Beschleunigung in g (Sensorbereich ±16 g; Erdbeschleunigung ~1 g
    # liegt mit ~9 sichtbar in Ruhe-daten), Gyroskop in °/s (Spec ±2000),
    # Magnetometer in µT (Erdmagnetfeld ~25–65 µT, Hard-Iron-Offsets
    # möglich → großzügiger Bereich).
    "accx":             (-16.0, 16.0),
    "accy":             (-16.0, 16.0),
    "accz":             (-16.0, 16.0),
    "accwrx":           (-16.0, 16.0),
    "accwry":           (-16.0, 16.0),
    "accwrz":           (-16.0, 16.0),
    "gyrox":            (-2000.0, 2000.0),
    "gyroy":            (-2000.0, 2000.0),
    "gyroz":            (-2000.0, 2000.0),
    "magx":             (-400.0, 400.0),
    "magy":             (-400.0, 400.0),
    "magz":             (-400.0, 400.0),
    # EEG/OpenBCI (Reservierung, AP8: keine negativen/absurden Amplituden;
    # Rohwerte in µV, typisch ±100 µV, Artefakte bis ~±4000 µV)
    "eeg":              (-4000.0, 4000.0),
    "eeg1":             (-4000.0, 4000.0),
    "eeg2":             (-4000.0, 4000.0),
    "eeg3":             (-4000.0, 4000.0),
    "eeg4":             (-4000.0, 4000.0),
    "eeg5":             (-4000.0, 4000.0),
    "eeg6":             (-4000.0, 4000.0),
    "eeg7":             (-4000.0, 4000.0),
    "eeg8":             (-4000.0, 4000.0),
    "openbci":          (-4000.0, 4000.0),
}

# Normalisierte Key-Form (klein, ohne '_'/'-') für exaktes Matching
_PLAUSIBILITY_NORM: dict[str, tuple[float, float]] = {
    k.replace("_", "").replace("-", ""): v for k, v in _PLAUSIBILITY.items()
}


def _plausibility_for_channel(ch_name: str) -> tuple[float, float] | None:
    """
    Plausibilitäts-Range für einen Kanalnamen, oder None.

    Ein Kanal passt, wenn eines seiner Punkt-Segmente (normalisiert:
    klein, ohne '_'/'-') EXAKT einem Key entspricht — 'gaze.LeftX' →
    'leftx', 'heart_rate' → 'heartrate'. Bewusst kein Substring-Matching:
    'hr' würde sonst auch 'hrv' (RMSSD in ms) und 'threshold' (Bool-Flag)
    treffen und korrekte Daten als außerhalb der Range markieren.
    """
    for seg in ch_name.split("."):
        norm = seg.lower().replace("_", "").replace("-", "").strip()
        if norm in _PLAUSIBILITY_NORM:
            return _PLAUSIBILITY_NORM[norm]
    return None


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

        plausible_range = _plausibility_for_channel(ch_name)
        if plausible_range:
            lo, hi = plausible_range
            n_out = sum(1 for v in values if v is not None and not (lo <= float(v) <= hi))
            if n_out > 0:
                ch_issues.append(f"{n_out} value(s) outside plausible range [{lo}, {hi}]")

        if n_missing > 0:
            ch_issues.append(f"{n_missing} missing value(s)")

        # Channel outage: long consecutive identical non-null values.
        # None-Runs zählen NICHT als Outage (sie sind schon in n_missing
        # erfasst) – hier geht es um konstante, aber vorhandene Werte.
        # Skip binary channels (only 0/1) – validity flags are expected to be constant
        unique_vals = set(str(v) for v in values if v is not None)
        is_binary = unique_vals <= {"0", "1", "0.0", "1.0"}
        if not is_binary:
            sentinel = object()
            prev: object = sentinel
            run = 0
            max_streak = 0
            for v in values:
                if v is None:
                    run = 0            # Lücke: kein Outage, zählt als n_missing
                elif v == prev:
                    run += 1
                    max_streak = max(max_streak, run)
                else:
                    run = 1
                    max_streak = max(max_streak, run)
                prev = v
            # Only flag if streak covers >5% of total samples and is at least 50 samples
            # (avoids false positives from sensor fusion at mismatched rates)
            outage_threshold = max(50, int(len(values) * 0.05))
            if max_streak >= outage_threshold:
                ch_issues.append(f"Constant-value streak of {max_streak} samples (possible outage)")

        # Duplicate Werte innerhalb des Kanals (ohne None — das ist n_missing);
        # Hinweis: bei langsamen, gerundeten Signalen sind Wiederholungen normal,
        # daher nur ein Metrik-Wert, kein Issue.
        n_dups = len([v for v in values if v is not None]) - len(
            set(str(v) for v in values if v is not None)
        )

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
