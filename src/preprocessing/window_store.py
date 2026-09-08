"""AP6 – Versioned, persistent storage for window definitions.

Window definitions are serialised to a JSON file (default:
``window_definitions.json`` in the working directory). Every save appends a
new *version* entry under a stable ``name`` so later analyses stay
reproducible: parameters are never mutated in place, the full history is
kept, and any saved version can be reloaded verbatim.

File format::

    {
      "next_id": 3,
      "definitions": [
        {"id": 1, "name": "baseline_2s", "version": 1,
         "created_at": "2026-09-08T10:14:03", "params": {…WindowDefinition fields…}},
        {"id": 2, "name": "baseline_2s", "version": 2, …}
      ]
    }
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.models.experiment_records import WindowDefinition

DEFAULT_STORE_PATH = Path("window_definitions.json")

_FIELDS = ("window_id", "mode", "duration_ms", "step_ms", "task_label",
           "offset_start_ms", "offset_end_ms", "meta")


def definition_to_dict(d: WindowDefinition) -> dict[str, Any]:
    """Serialise a WindowDefinition into a JSON-safe dict."""
    out = {f: getattr(d, f) for f in _FIELDS}
    out["duration_ms"] = float(d.duration_ms)
    for k in ("step_ms", "offset_start_ms", "offset_end_ms"):
        if out[k] is not None:
            out[k] = float(out[k])
    return out


def definition_from_dict(data: dict[str, Any]) -> WindowDefinition:
    """Rebuild a WindowDefinition from a stored params dict."""
    return WindowDefinition(
        window_id=str(data["window_id"]),
        mode=str(data["mode"]),
        duration_ms=float(data["duration_ms"]),
        step_ms=float(data["step_ms"]) if data.get("step_ms") is not None else None,
        task_label=data.get("task_label"),
        offset_start_ms=float(data.get("offset_start_ms") or 0.0),
        offset_end_ms=float(data.get("offset_end_ms") or 0.0),
        meta=data.get("meta") or {},
    )


class WindowDefinitionStore:
    """Append-only, versioned store of WindowDefinitions in a JSON file."""

    def __init__(self, path: str | Path = DEFAULT_STORE_PATH) -> None:
        self.path = Path(path)

    # ── Low-level file access ─────────────────────────────────────────────────

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"next_id": 1, "definitions": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"next_id": 1, "definitions": []}
        data.setdefault("next_id", len(data.get("definitions", [])) + 1)
        data.setdefault("definitions", [])
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def save(self, name: str, definition: WindowDefinition) -> dict[str, Any]:
        """
        Save ``definition`` as a new version under ``name``.
        Returns the stored entry (with id, version, created_at).
        """
        if not name.strip():
            raise ValueError("Name für Fensterdefinition darf nicht leer sein.")
        data = self._read()
        versions = [e["version"] for e in data["definitions"] if e["name"] == name]
        entry = {
            "id": data["next_id"],
            "name": name.strip(),
            "version": max(versions, default=0) + 1,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "params": definition_to_dict(definition),
        }
        data["next_id"] += 1
        data["definitions"].append(entry)
        self._write(data)
        return entry

    def list_entries(self, name: str | None = None) -> list[dict[str, Any]]:
        """All stored entries, newest first; optionally filtered by name."""
        entries = self._read()["definitions"]
        if name is not None:
            entries = [e for e in entries if e["name"] == name]
        return sorted(entries, key=lambda e: (-e["version"], -e["id"]))

    def load(self, entry_id: int) -> WindowDefinition | None:
        """Rebuild the WindowDefinition of a stored entry (by id)."""
        for entry in self._read()["definitions"]:
            if entry["id"] == entry_id:
                return definition_from_dict(entry["params"])
        return None

    def delete(self, entry_id: int) -> bool:
        """Remove one entry. Returns True if it existed."""
        data = self._read()
        before = len(data["definitions"])
        data["definitions"] = [e for e in data["definitions"] if e["id"] != entry_id]
        if len(data["definitions"]) == before:
            return False
        self._write(data)
        return True
