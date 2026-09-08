"""
Reproduziert alle Kennzahlen aus Paper 2 (Webkomplexität) aus
new_web_features.csv: Tabellen 1–6, k-Scan, Baseline, Dekorrelations-
Analyse, Feature-Importance (MDI + Permutation), CV/Split, Silhouette-
Bootstrap und Cluster-Stabilität — jeweils mit dokumentierten Seeds.

Nicht reproduzierbar: Tabellen 7/8 (HTTP-Antwortzeiten). Die Messdaten
(3 Wiederholungen, Median, je Seite) wurden nicht archiviert; die im
Paper berichteten Werte beruhen auf der verlorenen Messung und sind dort
als solche gekennzeichnet.

Alle seeds sind fest dokumentiert; eine Änderungändert die Stabilitäts-
und Permutations-Zahlen (seed-abhängige Größen).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

CSV = Path("new_web_features.csv")
FEATS = ["link_count", "form_count", "media_count", "text_length", "dom_depth", "dom_nodes"]
DECORR = ["link_count", "dom_depth", "media_count", "form_count"]

SEED_KMEANS = 42
SEED_RF = 42
SEED_PERM = 42
SEED_SPLIT = 42          # ohne stratify — mit stratify ergäbe sich 0,833 statt 1,000
SEED_BOOTSTRAP = 42
SEED_STABILITY = 0
N_BOOTSTRAP = 1_000
N_STABILITY = 50


def load(csv: Path | str = CSV) -> pd.DataFrame:
    return pd.read_csv(csv)


def _kmeans(X, k: int = 3, seed: int = SEED_KMEANS):
    return KMeans(n_clusters=k, random_state=seed, n_init=10).fit_predict(X)


def cluster_analysis(df: pd.DataFrame) -> dict:
    X = StandardScaler().fit_transform(df[FEATS])
    labels = _kmeans(X)
    return {
        "labels": labels,
        "silhouette": silhouette_score(X, labels),
        "ari_website": adjusted_rand_score(df["website"], labels),
        "cluster_means": df.assign(cluster=labels).groupby("cluster")[FEATS].mean(),
        "contingency": pd.crosstab(df["website"], labels),
    }


def k_scan(df: pd.DataFrame) -> dict[int, float]:
    X = StandardScaler().fit_transform(df[FEATS])
    return {k: float(silhouette_score(X, _kmeans(X, k)))
            for k in range(2, 7)}


def baseline(df: pd.DataFrame) -> dict:
    X = StandardScaler().fit_transform(df[["link_count"]])
    labels = _kmeans(X)
    full = _kmeans(StandardScaler().fit_transform(df[FEATS]))
    return {
        "silhouette": float(silhouette_score(X, labels)),
        "ari_to_full": float(adjusted_rand_score(full, labels)),
    }


def decorrelation(df: pd.DataFrame) -> dict:
    """K-Means auf dem dekorrelierten Merkmalssatz (ohne text_length und
    dom_nodes, die mit r = 0,81/0,72 an link_count hängen)."""
    X = StandardScaler().fit_transform(df[DECORR])
    labels = _kmeans(X)
    full = _kmeans(StandardScaler().fit_transform(df[FEATS]))
    base = _kmeans(StandardScaler().fit_transform(df[["link_count"]]))
    return {
        "silhouette": float(silhouette_score(X, labels)),
        "sizes": np.bincount(labels).tolist(),
        "ari_to_full": float(adjusted_rand_score(full, labels)),
        "ari_to_baseline": float(adjusted_rand_score(base, labels)),
        "contingency": pd.crosstab(df["website"], labels),
        "cluster_means": df.assign(cluster=labels).groupby("cluster")[FEATS].mean(),
    }


def importance_and_cv(df: pd.DataFrame, labels) -> dict:
    X, y = df[FEATS], labels
    rf = RandomForestClassifier(n_estimators=100, random_state=SEED_RF).fit(X, y)
    perm = permutation_importance(rf, X, y, n_repeats=30, random_state=SEED_PERM)
    cv = cross_val_score(RandomForestClassifier(n_estimators=100, random_state=SEED_RF), X, y, cv=5)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25,
                                          random_state=SEED_SPLIT)  # ohne stratify
    split_acc = RandomForestClassifier(n_estimators=100, random_state=SEED_RF) \
        .fit(Xtr, ytr).score(Xte, yte)
    return {
        "mdi": dict(zip(FEATS, rf.feature_importances_.round(3))),
        "perm": dict(zip(FEATS, perm.importances_mean.round(3))),
        "cv_folds": [round(float(v), 3) for v in cv],
        "cv_mean": float(cv.mean()),
        "split_acc": float(split_acc),
    }


def silhouette_bootstrap(df: pd.DataFrame, seed: int = SEED_BOOTSTRAP,
                         n: int = N_BOOTSTRAP) -> tuple[float, float, float]:
    X = StandardScaler().fit_transform(df[FEATS])
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(n):
        idx = rng.choice(len(X), size=len(X), replace=True)
        Xb = X[idx]
        lab = _kmeans(Xb)
        if len(set(lab)) > 1:
            scores.append(silhouette_score(Xb, lab))
    s = np.array(scores)
    return float(s.mean()), float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


def stability(df: pd.DataFrame, seed: int = SEED_STABILITY,
              n: int = N_STABILITY) -> tuple[float, float]:
    X = StandardScaler().fit_transform(df[FEATS])
    ref = _kmeans(X)
    rng = np.random.default_rng(seed)
    aris = [adjusted_rand_score(ref, _kmeans(X, seed=int(s)))
            for s in rng.integers(1, 100_000, n)]
    return float(np.mean(aris)), float(np.min(aris))


def stratified_cv(df: pd.DataFrame, labels) -> dict:
    """StratifiedKFold-Variante (5 Folds, Seed 42) plus balancierte
    Accuracy der out-of-fold-Vorhersagen — Ergänzung zur unstratifizierten
    Standard-CV, da die Cluster stark unbalanciert sind (30/6/11)."""
    from sklearn.metrics import balanced_accuracy_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rf = RandomForestClassifier(n_estimators=100, random_state=SEED_RF)
    acc = cross_val_score(rf, df[FEATS], labels, cv=skf)
    pred = cross_val_predict(rf, df[FEATS], labels, cv=skf)
    return {
        "folds": [round(float(v), 3) for v in acc],
        "mean": float(acc.mean()),
        "balanced_accuracy": float(balanced_accuracy_score(labels, pred)),
    }


def log_transform_clustering(df: pd.DataFrame) -> dict:
    """Robustheitsvariante gegen die Rechtsschiefe von link_count und
    text_length: log1p vor der z-Standardisierung."""
    Xlog = StandardScaler().fit_transform(np.log1p(df[FEATS]))
    labels_log = _kmeans(Xlog)
    ref = _kmeans(StandardScaler().fit_transform(df[FEATS]))
    return {
        "silhouette": float(silhouette_score(Xlog, labels_log)),
        "ari_to_untransformed": float(adjusted_rand_score(ref, labels_log)),
    }


def make_figures(df: pd.DataFrame, labels, out_dir: Path = Path("figures")) -> None:
    out_dir.mkdir(exist_ok=True)
    # Abbildung 1: Merkmalsverteilung (M ± SD, skaliert wie im Paper)
    means = [df[f].mean() for f in FEATS]
    sds = [df[f].std(ddof=1) for f in FEATS]
    scale = [1, 1, 1, 100, 1, 10]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(FEATS, [m / s for m, s in zip(means, scale)],
           yerr=[sd / s for sd, s in zip(sds, scale)], capsize=4, color="#4C72B0")
    ax.set_ylabel("Mittelwert ± SD (text_length ÷ 100, dom_nodes ÷ 10)")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(out_dir / "paper2_abb1_feature_distribution_v2.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Abbildung 2: DOM-Tiefe × Links nach Cluster mit Zentren
    scaler = StandardScaler()
    X = scaler.fit_transform(df[FEATS])
    km = KMeans(n_clusters=3, random_state=SEED_KMEANS, n_init=10).fit(X)
    # Zentren zurück in Roheinheiten transformieren — im z-Raum geplottet
    # lägen die Sterne bei ~0 und damit weit außerhalb der Punktwolken
    centers_raw = scaler.inverse_transform(km.cluster_centers_)
    fig, ax = plt.subplots(figsize=(8, 6))
    for c in range(3):
        m = labels == c
        ax.scatter(df.loc[m, "dom_depth"], df.loc[m, "link_count"],
                   s=45, alpha=0.75, label=f"Cluster {c}")
    ax.scatter(centers_raw[:, FEATS.index("dom_depth")], centers_raw[:, FEATS.index("link_count")],
               marker="*", s=350, color="black", label="Zentrum")
    ax.set_xlabel("dom_depth")
    ax.set_ylabel("link_count")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "paper2_abb2_cluster_scatter_v2.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = load()
    print(f"N = {len(df)} Seiten, Websites: {df['website'].value_counts().to_dict()}\n")

    print("Tabelle 1 (Merkmalsverteilung):")
    for f in FEATS:
        print(f"  {f:12} M={df[f].mean():9.2f} SD={df[f].std():7.2f} "
              f"min={df[f].min():6.0f} max={df[f].max():6.0f}")

    print("\nTabelle 6 (Website-Mittelwerte):")
    print(df.groupby("website")[FEATS].mean().round(1).to_string())

    ca = cluster_analysis(df)
    print(f"\nSilhouette k=3: {ca['silhouette']:.3f} | ARI Cluster×Website: {ca['ari_website']:.3f}")
    print("Tabelle 3 (Kreuztabelle):")
    print(ca["contingency"].to_string())
    print("Tabelle 2 (Cluster-Mittelwerte):")
    print(ca["cluster_means"].round(1).to_string())

    print("\nk-Scan:", {k: round(v, 3) for k, v in k_scan(df).items()})
    b = baseline(df)
    print(f"Baseline link_count: Silhouette {b['silhouette']:.3f}, ARI zu 6-Merkmal {b['ari_to_full']:.3f}")

    d = decorrelation(df)
    print(f"\nDekorrelation ({', '.join(DECORR)}): Silhouette {d['silhouette']:.3f}, "
          f"Sizes {d['sizes']}, ARI zu 6-Merkmal {d['ari_to_full']:.3f}, "
          f"ARI zu Baseline {d['ari_to_baseline']:.3f}")
    print(d["contingency"].to_string())

    imp = importance_and_cv(df, ca["labels"])
    print("\nTabelle 5 (MDI / Permutation):")
    for f in FEATS:
        print(f"  {f:12} MDI={imp['mdi'][f]:.3f}  Perm={imp['perm'][f]:.3f}")
    print(f"Tabelle 4: CV-Folds {imp['cv_folds']} (M {imp['cv_mean']:.3f}), "
          f"Einzel-Split ohne stratify: {imp['split_acc']:.3f}")

    m, lo, hi = silhouette_bootstrap(df)
    print(f"\nSilhouette-Bootstrap: M={m:.3f}, 95%-CI [{lo:.3f}, {hi:.3f}]")
    smean, smin = stability(df)
    print(f"Cluster-Stabilität (50 Seeds, rng(0)): M={smean:.3f}, min={smin:.3f}")

    scv = stratified_cv(df, ca["labels"])
    print(f"StratifiedKFold-CV: {scv['folds']} (M {scv['mean']:.3f}), "
          f"balancierte Accuracy {scv['balanced_accuracy']:.3f}")
    lt = log_transform_clustering(df)
    print(f"Log-Transform: Silhouette {lt['silhouette']:.3f}, "
          f"ARI zur untransformierten Lösung {lt['ari_to_untransformed']:.3f}")

    c = df[FEATS].corr().round(2)
    print(f"Korrelationen: r(link,text)={c.loc['link_count', 'text_length']}, "
          f"r(link,nodes)={c.loc['link_count', 'dom_nodes']}")

    make_figures(df, ca["labels"])
    print("\nAbbildungen geschrieben: figures/paper2_abb1_..._v2.png, paper2_abb2_..._v2.png")
    print("HINWEIS: Tabellen 7/8 (Antwortzeit) sind hier NICHT reproduzierbar — "
          "Messdaten wurden nicht archiviert (s. Paper, 4.6/Verfügbarkeit).")


if __name__ == "__main__":
    main()
