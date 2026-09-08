"""Shared folder-name sorting for trial/website directory scans."""

from __future__ import annotations

import re


def natural_sort_key(name: str) -> tuple[int, str]:
    """Sort folder names numerically on their leading/embedded digits, falling
    back to alphabetical order when no digits are present (e.g. "trial_02b" → 2)."""
    m = re.search(r"\d+", name)
    return (int(m.group()) if m else 0, name)
