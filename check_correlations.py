"""
Berechnet Pearson-Korrelation: Taskdauer vs. NASA-TLX Frustration & Mentale Last.
Gibt r-Werte aus und speichert neues Scatterplot unter figures/paper1_abb2_scatter_duration_tlx.png
"""

import json
import os
from pathlib import Path
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'

DATA_DIR = Path("data")
DOMAIN_MAP = {"gaming": "Gaming", "health": "Gesundheit", "city": "Stadtplanung"}
COLORS = {"gaming": "#4C72B0", "health": "#55A868", "city": "#C44E52"}

records = []

for trial_dir in sorted(DATA_DIR.iterdir()):
    events_file = trial_dir / "events.ndjson"
    if not events_file.exists():
        continue

    events = []
    with open(events_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    # TLX scores per domain
    tlx = {}
    for e in events:
        if e.get("type") == "tlx:submit":
            domain = e.get("domain")
            if domain and "scores" in e:
                tlx[domain] = e["scores"]

    # Task durations per domain (sum of all task segments)
    task_starts = {}
    task_durations = {}
    for e in events:
        domain = e.get("domain")
        if not domain:
            continue
        if e.get("type") == "task:start":
            task_starts[domain] = e["ts"]
        elif e.get("type") == "task:end" and domain in task_starts:
            dur = (e["ts"] - task_starts[domain]) / 1000  # ms → s
            task_durations[domain] = task_durations.get(domain, 0) + dur
            del task_starts[domain]

    for domain in tlx:
        if domain in task_durations:
            records.append({
                "trial": trial_dir.name,
                "domain": domain,
                "duration_s": task_durations[domain],
                "frustration": tlx[domain].get("frustration"),
                "mentale": tlx[domain].get("mentale"),
            })

print(f"Datenpunkte gesamt: {len(records)}")

durations = np.array([r["duration_s"] for r in records])
frustrations = np.array([r["frustration"] for r in records])
mentale = np.array([r["mentale"] for r in records])

# Ausreißer entfernen (> 3 SD bei Dauer)
mean_d, std_d = durations.mean(), durations.std()
mask = np.abs(durations - mean_d) <= 3 * std_d
print(f"Ausreißer entfernt: {(~mask).sum()}")

d_clean = durations[mask]
f_clean = frustrations[mask]
m_clean = mentale[mask]

r_frust, p_frust = stats.pearsonr(d_clean, f_clean)
r_mental, p_mental = stats.pearsonr(d_clean, m_clean)

print(f"\nPearson r (Dauer × Frustration): r = {r_frust:.3f}, p = {p_frust:.4f}")
print(f"Pearson r (Dauer × Mentale Last): r = {r_mental:.3f}, p = {p_mental:.4f}")

# ── Plot: zwei separate Bilder ────────────────────────────────────────────────
domains_clean = [r["domain"] for r, m in zip(records, mask) if m]

plots = [
    ("frustration", "Frustration (0--100)", r_frust, "paper1_scatter_frustration.png"),
    ("mentale",     "Mentale Anforderung (0--100)", r_mental, "paper1_scatter_mentale.png"),
]

for tlx_key, label, r_val, filename in plots:
    fig, ax = plt.subplots(figsize=(8, 6))
    scores_clean = np.array([r[tlx_key] for r, m in zip(records, mask) if m])

    for domain, color in COLORS.items():
        idx = [i for i, d in enumerate(domains_clean) if d == domain]
        ax.scatter(d_clean[idx], scores_clean[idx],
                   color=color, alpha=0.7, s=60, label=DOMAIN_MAP[domain])
        if len(idx) >= 2:
            m_fit, b_fit = np.polyfit(d_clean[idx], scores_clean[idx], 1)
            x_line = np.linspace(d_clean[idx].min(), d_clean[idx].max(), 100)
            ax.plot(x_line, m_fit * x_line + b_fit, color=color, alpha=0.5, linewidth=1.5)

    m_tot, b_tot = np.polyfit(d_clean, scores_clean, 1)
    x_all = np.linspace(d_clean.min(), d_clean.max(), 100)
    ax.plot(x_all, m_tot * x_all + b_tot, "k--", linewidth=2,
            label=f"Gesamt (r = {r_val:.2f})")

    ax.set_xlabel("Kumul. Aufgabendauer (s)", fontsize=12)
    ax.set_ylabel(label, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_title(f"Taskdauer x {label.split(' ')[0]}  (N = {mask.sum()})", fontsize=12)

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"Gespeichert: {filename}")
    plt.close()
