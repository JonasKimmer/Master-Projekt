"""
Reproduziert die inferenzstatistischen Kennzahlen aus Paper 1 (Abschnitt
4.3): Bearbeitungszeit × NASA-TLX, korrigiert für Pseudoreplikation.

  * unkorrigierte Pearson-r je Dimension mit Fisher-z-Konfidenzintervall
  * innerhalb-Person-zentrierte Korrelation (Subtraktion der Personen-
    mittelwerte von Dauer und Dimension)
  * personen-geclusterter Bootstrap (5.000 Resamples, fester Seed) für
    das CI der zentrierten Korrelation
  * gemischtes Modell (statsmodels MixedLM, Random Intercept pro Person)
    mit Slope, 95 %-CI und p-Wert

Datengrundlage ist derselbe Vertrag wie check_correlations.py
(trial_loader-Aliase, Restart-Paarungslogik, globaler >3-SD-Ausreißer-
Ausschluss auf der kumulierten Dauer — betrifft T-4/Gesundheit).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats as st

import check_correlations as cc

DATA_DIR = Path("data")
DIMS = ("frustration", "mentale", "anstrengung")
BOOT_N = 5_000
SEED = 42


def build_frame(data_dir: Path | str = DATA_DIR) -> pd.DataFrame:
    """Datensatz wie in Paper 1, Tabelle 3: N = 53 Domänendurchläufe."""
    records = cc.complete_records(cc.collect_records(data_dir))
    df = pd.DataFrame(records)
    df = df.rename(columns={"trial": "person"})
    # Globaler >3-SD-Ausschluss auf der kumulierten Dauer (wie Skript/Paper)
    d = df["duration_s"].to_numpy()
    mask = np.abs(d - d.mean()) <= 3 * d.std()
    return df[mask].reset_index(drop=True)


def fisher_ci(r: float, n: int) -> tuple[float, float]:
    """95 %-CI einer Korrelation via Fisher-z-Transformation."""
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    return float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se))


def centered_r(df: pd.DataFrame, dim: str) -> float:
    """Pearson-r nach within-Person-Zentrierung von Dauer und Dimension."""
    c = df.copy()
    c["duration_s"] = c.groupby("person")["duration_s"].transform(lambda x: x - x.mean())
    c[dim] = c.groupby("person")[dim].transform(lambda x: x - x.mean())
    c = c.dropna(subset=["duration_s", dim])
    return float(st.pearsonr(c["duration_s"], c[dim])[0])


def clustered_bootstrap_ci(df: pd.DataFrame, dim: str,
                           n_resamples: int = BOOT_N, seed: int = SEED) -> tuple[float, float]:
    """95 %-Percentil-CI der zentrierten Korrelation; Resampling der PERSONEN
    (nicht der Domänendurchläufe), damit die Clusterstruktur erhalten bleibt."""
    rng = np.random.default_rng(seed)
    persons = df["person"].unique()
    rs = []
    for _ in range(n_resamples):
        sample = rng.choice(persons, size=len(persons), replace=True)
        parts = [df[df["person"] == p] for p in sample]
        # Personen können mehrfach gezogen werden: Kennzahlen-zentriert
        # berechnen wir je Draw über die verkettete (gepoolte) Auswahl;
        # Doppelziehungen fließen mehrfach ein, wie beim Cluster-Bootstrap üblich.
        b = pd.concat(parts)
        if b["duration_s"].std() > 0 and b[dim].std() > 0:
            rs.append(centered_r(b, dim))
    lo, hi = np.percentile(rs, [2.5, 97.5])
    return float(lo), float(hi)


def mixed_model(df: pd.DataFrame, dim: str) -> dict:
    model = smf.mixedlm(f"{dim} ~ duration_s", df, groups=df["person"])
    res = model.fit(reml=False)
    ci = res.conf_int().loc["duration_s"]
    return {
        "slope": float(res.params["duration_s"]),
        "ci": (float(ci[0]), float(ci[1])),
        "p": float(res.pvalues["duration_s"]),
    }


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
    df = build_frame(DATA_DIR)
    print(f"N = {len(df)} Domänendurchläufe von {df['person'].nunique()} Personen\n")
    print(f"{'Dimension':16} {'r':>6} {'CI (Fisher)':>16} {'r (zentriert)':>14} "
          f"{'CI (Bootstrap)':>16} {'Slope':>8} {'MixedLM-CI':>18} {'p':>9}")
    for dim in DIMS:
        r = float(st.pearsonr(df["duration_s"], df[dim])[0])
        rc = centered_r(df, dim)
        mm = mixed_model(df, dim)
        print(f"{dim:16} {r:6.2f} [{fisher_ci(r, len(df))[0]:5.2f}, {fisher_ci(r, len(df))[1]:4.2f}]"
              f" {rc:14.2f} [{clustered_bootstrap_ci(df, dim)[0]:5.2f}, {clustered_bootstrap_ci(df, dim)[1]:4.2f}]"
              f" {mm['slope']:8.3f} [{mm['ci'][0]:.3f}, {mm['ci'][1]:.3f}] {mm['p']:9.4f}")


if __name__ == "__main__":
    main()
