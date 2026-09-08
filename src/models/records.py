"""Base records shared across all data domains."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DatasetRecord:
    """Uploaded tabular dataset (CSV / Excel / JSON)."""

    name: str
    source_path: str | None = None
    raw_json: Any = None
    # DataFrame is stored in session state, not here, to avoid serialisation issues.
    # Use session.get_tabular() to retrieve it.
    meta: dict[str, Any] = field(default_factory=dict)
