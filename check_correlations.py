"""
Berechnet Pearson-Korrelation: Taskdauer vs. NASA-TLX Frustration & Mentale Last.
Gibt r-Werte aus und speichert zwei Scatterplots im Projekt-Root
(paper1_scatter_frustration.png, paper1_scatter_mentale.png) sowie die
kombinierte Zwei-Panel-Abbildung figures/paper1_abb2_scatter_duration_tlx.png.

Event-Parsing läuft über den trial_loader-Vertrag (dieselben Timestamp-
Aliase wie ts/timestamp/timestamp_ms/… und Label-Keys wie type/event/
label/… wie in der gesamten App) — keine eigene Importlogik mehr, die
bei Alias-Daten still leere Ergebnisse liefert.

Bewusste Abweichung von der segmentation-FIFO-Paarung: Dauern werden
mit 'neuester offener Start gewinnt' gerechnet (Restart-Annahme). Ein
verwaister Start ohne End (z. B. T-3/city: 824 s Lücke vor dem ersten
task:end) wird so verworfen statt der Taskdauer zugeschlagen. Das ist
die Semantik, mit der die in Paper 1 berichteten Werte (r = 0,56 /
0,03) berechnet wurden — Umstellen auf build_timeline würde diese
Zahlen verschieben (r = 0,43 / -0,11).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Headless: Skript erzeugt Dateien, kein Fenster
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from src.loaders.trial_loader import load_trials_from_dir

DATA_DIR = Path("data")
DOMAIN_MAP = {"gaming": "Gaming", "health": "Gesundheit", "city": "Stadtplanung"}
COLORS = {"gaming": "#4C72B0", "health": "#55A868", "city": "#C44E52"}


def collect_records(data_dir: Path | str = DATA_DIR) -> list[dict]:
    """Pro Trial und Domain: kumulierte Taskdauer + TLX-Scores.

    Parsing über load_trials_from_dir (Alias-Vertrag). Nur Domains mit
    sowohl Dauer (mindestens einem vollständigen Start/End-Paar) als
    auch TLX-Submit landen im Ergebnis.
    """
    records: list[dict] = []
    for trial in load_trials_from_dir(str(data_dir)):
        # Taskdauer pro Domain; ein neuer task:start derselben Domain
        # ersetzt einen noch offenen Start (Restart, siehe Modul-Docstring)
        task_starts: dict[object, float] = {}
        task_durations: dict[object, float] = {}
        for e in trial.events:
            domain = e.meta.get("domain")
            if not domain:
                continue
            label = e.label.lower()
            if label == "task:start":
                task_starts[domain] = e.timestamp
            elif label == "task:end" and domain in task_starts:
                task_durations[domain] = (
                    task_durations.get(domain, 0.0)
                    + (e.timestamp - task_starts[domain]) / 1000.0
                )
                del task_starts[domain]

        tlx: dict[object, dict] = {}
        for e in trial.events:
            if e.label.lower() == "tlx:submit":
                domain = e.meta.get("domain")
                scores = e.meta.get("scores")
                if domain and isinstance(scores, dict):
                    tlx[domain] = scores

        for domain, scores in tlx.items():
            if domain in task_durations:
                records.append({
                    "trial": trial.trial_id,
                    "domain": domain,
                    "duration_s": task_durations[domain],
                    "frustration": scores.get("frustration"),
                    "mentale": scores.get("mentale"),
                    "anstrengung": scores.get("anstrengung"),
                })
    return records


def complete_records(records: list[dict]) -> list[dict]:
    """Nur Datensätze mit numerischen TLX-Werten (als float).

    Fehlende Werte (None) oder nicht-numerische Einträge würden pearsonr
    mit object-Arrays crashen bzw. still nan liefern — sie werden hier
    sichtbar gefiltert statt mitzurechnen.
    """
    dims = ("frustration", "mentale", "anstrengung")
    out: list[dict] = []
    for r in records:
        try:
            coerced = {d: float(r[d]) for d in dims}
        except (TypeError, ValueError, KeyError):
            continue
        out.append({**r, **coerced})
    return out


def _scatter_panel(ax, records: list[dict], mask: np.ndarray, tlx_key: str,
                   label: str, r_val: float) -> None:
    """Ein Streudiagramm-Panel: Dauer × TLX-Dimension, farbig nach Domäne,
    Regressionsgeraden je Domäne und gesamt."""
    d_clean = np.array([r["duration_s"] for r, m in zip(records, mask) if m])
    scores = np.array([r[tlx_key] for r, m in zip(records, mask) if m])
    domains = [r["domain"] for r, m in zip(records, mask) if m]

    for domain, color in COLORS.items():
        idx = [i for i, d in enumerate(domains) if d == domain]
        ax.scatter(d_clean[idx], scores[idx],
                   color=color, alpha=0.7, s=60, label=DOMAIN_MAP[domain])
        if len(idx) >= 2:
            m_fit, b_fit = np.polyfit(d_clean[idx], scores[idx], 1)
            x_line = np.linspace(d_clean[idx].min(), d_clean[idx].max(), 100)
            ax.plot(x_line, m_fit * x_line + b_fit, color=color, alpha=0.5, linewidth=1.5)

    m_tot, b_tot = np.polyfit(d_clean, scores, 1)
    x_all = np.linspace(d_clean.min(), d_clean.max(), 100)
    ax.plot(x_all, m_tot * x_all + b_tot, "k--", linewidth=2,
            label=f"Gesamt (r = {r_val:.2f})")

    ax.set_xlabel("Kumul. Aufgabendauer (s)", fontsize=12)
    ax.set_ylabel(label, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_title(f"Taskdauer x {label.split(' ')[0]}  (N = {int(mask.sum())})", fontsize=12)


VIZ_ORDER = ("Timeline", "Scatter", "Combo", "Heatmap", "Dashboard")


def position_durations(data_dir: Path | str = DATA_DIR) -> dict[str, list[float]]:
    """Aufgabendauern je Position innerhalb des Domänenblocks (= Visualisierungs-
    typ, da feste Reihenfolge). Nutzt dieselbe Restart-Paarung wie
    collect_records; Rückgabe {Position: [Dauern in s]}."""
    from collections import defaultdict

    durs: dict[str, list[float]] = defaultdict(list)
    for trial in load_trials_from_dir(str(data_dir)):
        starts: dict[object, float] = {}
        pairs: dict[object, list[tuple[float, float]]] = defaultdict(list)
        for e in trial.events:
            domain = e.meta.get("domain")
            if not domain:
                continue
            label = e.label.lower()
            if label == "task:start":
                starts[domain] = e.timestamp
            elif label == "task:end" and domain in starts:
                pairs[domain].append((starts[domain], e.timestamp))
                del starts[domain]
        for plist in pairs.values():
            for i, (a, b) in enumerate(sorted(plist)):
                if i < len(VIZ_ORDER):
                    durs[VIZ_ORDER[i]].append((b - a) / 1000.0)
    return durs


def _require_data() -> bool:
    if not DATA_DIR.exists():
        print(f"Hinweis: {DATA_DIR} fehlt — die Experiment-Rohdaten sind aus "
              "Datenschutzgründen nicht Teil des Repos (s. Paper 1, "
              "Verfügbarkeitsstatement). Skript wird übersprungen.")
        return False
    return True

def main() -> None:
    if not _require_data():
        return
    # Bearbeitungszeit je Aufgabenposition (= Visualisierungstyp, Tabelle 2b)
    import numpy as np
    durs = position_durations()
    print("Bearbeitungszeit je Aufgabenposition (Restart-Paarung):")
    for i, viz in enumerate(VIZ_ORDER):
        a = np.array(durs[viz])
        print(f"  {i+1} {viz:10} M={a.mean():6.1f} s  SD={a.std(ddof=1):6.1f}  n={len(a)}")

    records = complete_records(collect_records(DATA_DIR))
    print(f"Datenpunkte gesamt (mit vollständigen TLX-Werten): {len(records)}")
    if len(records) < 2:
        print("Zu wenige Datenpunkte für Korrelation — Abbruch.")
        return

    durations = np.array([r["duration_s"] for r in records])
    frustrations = np.array([r["frustration"] for r in records])
    mentale = np.array([r["mentale"] for r in records])

    # Ausreißer entfernen (> 3 SD bei Dauer)
    mean_d, std_d = durations.mean(), durations.std()
    if std_d == 0:
        mask = np.ones(len(durations), dtype=bool)
    else:
        mask = np.abs(durations - mean_d) <= 3 * std_d
    print(f"Ausreißer entfernt: {(~mask).sum()}")

    d_clean = durations[mask]
    f_clean = frustrations[mask]
    m_clean = mentale[mask]

    r_frust, p_frust = stats.pearsonr(d_clean, f_clean)
    r_mental, p_mental = stats.pearsonr(d_clean, m_clean)

    print(f"\nPearson r (Dauer × Frustration): r = {r_frust:.3f}, p = {p_frust:.4f}")
    print(f"Pearson r (Dauer × Mentale Last): r = {r_mental:.3f}, p = {p_mental:.4f}")

    # ── Plot: zwei separate Bilder ────────────────────────────────────────
    panels = [
        ("frustration", "Frustration (0--100)", r_frust, "paper1_scatter_frustration.png"),
        ("mentale",     "Mentale Anforderung (0--100)", r_mental, "paper1_scatter_mentale.png"),
    ]

    for tlx_key, label, r_val, filename in panels:
        fig, ax = plt.subplots(figsize=(8, 6))
        _scatter_panel(ax, records, mask, tlx_key, label, r_val)
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches="tight")
        print(f"Gespeichert: {filename}")
        plt.close(fig)

    # ── Kombinierte Zwei-Panel-Abbildung (Paper 1, Abbildung 2) ───────────
    # figures/paper1_abb2_scatter_duration_tlx.png wird von diesem Skript
    # erzeugt (früher: verwaistes Artefakt einer älteren Analyseversion).
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    _scatter_panel(ax1, records, mask, "frustration", "Frustration (0--100)", r_frust)
    _scatter_panel(ax2, records, mask, "mentale", "Mentale Anforderung (0--100)", r_mental)
    plt.tight_layout()
    out = Path("figures") / "paper1_abb2_scatter_duration_tlx.png"
    out.parent.mkdir(exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Gespeichert: {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()
