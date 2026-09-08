"""AP13 – Optional ML module on aggregated window/page features."""

from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, mean_absolute_error, r2_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


# ── Preprocessing ─────────────────────────────────────────────────────────────

def prepare_features(df: pd.DataFrame, drop_cols: list[str] | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Drop non-feature columns and return numeric-only feature matrix + column list.

    feature_names wird NACH dropna(axis=1, how="all") gebildet — die
    zurückgegebene Liste muss exakt den Spalten der Matrix entsprechen,
    sonst verrutscht jede Index-Zuordnung (Feature-Importances etc.).
    """
    numeric = df.select_dtypes(include="number").drop(
        columns=[c for c in (drop_cols or []) if c in df.columns], errors="ignore"
    )
    features = numeric.dropna(axis=1, how="all").fillna(0)
    return features, list(features.columns)


# ── Clustering ────────────────────────────────────────────────────────────────

def run_kmeans(df: pd.DataFrame, n_clusters: int = 3) -> dict:
    if len(df) < n_clusters:
        return {"error": f"Nur {len(df)} Zeile(n), aber n_clusters={n_clusters} verlangt."}
    X = StandardScaler().fit_transform(df)
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(X)
    score = silhouette_score(X, labels) if n_clusters > 1 else 0.0
    return {
        "labels": labels.tolist(),
        "silhouette": round(float(score), 4),
        "inertia": round(float(model.inertia_), 2),
        "n_clusters": n_clusters,
    }


# ── Anomaly Detection ─────────────────────────────────────────────────────────

def run_isolation_forest(df: pd.DataFrame, contamination: float = 0.05) -> dict:
    X = StandardScaler().fit_transform(df)
    model = IsolationForest(contamination=contamination, random_state=42)
    labels = model.fit_predict(X)
    n_anomalies = int((labels == -1).sum())
    return {
        "labels": labels.tolist(),   # -1 = anomaly, 1 = normal
        "n_anomalies": n_anomalies,
        "anomaly_rate": round(n_anomalies / len(labels), 4),
    }


# ── Classification ────────────────────────────────────────────────────────────

def run_classification(df: pd.DataFrame, target_col: str) -> dict:
    if target_col not in df.columns:
        return {"error": f"Column '{target_col}' not found."}

    X = df.drop(columns=[target_col]).select_dtypes(include="number").fillna(0)
    if X.shape[1] == 0:
        return {"error": "No numeric feature columns left after excluding the target."}
    y_raw = df[target_col]

    le = LabelEncoder()
    y = le.fit_transform(y_raw.astype(str))

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    importances = dict(zip(X.columns, model.feature_importances_.round(4)))
    top_features = dict(sorted(importances.items(), key=lambda x: -x[1])[:10])

    return {
        "report": classification_report(y_test, y_pred, labels=sorted(set(y_test)), target_names=[le.classes_[i] for i in sorted(set(y_test))], output_dict=True, zero_division=0),
        "top_features": top_features,
        "classes": list(le.classes_),
    }


# ── Regression ────────────────────────────────────────────────────────────────

def run_regression(df: pd.DataFrame, target_col: str) -> dict:
    if target_col not in df.columns:
        return {"error": f"Column '{target_col}' not found."}
    if not pd.api.types.is_numeric_dtype(df[target_col]):
        return {"error": f"Column '{target_col}' is not numeric — choose a numeric target for regression."}

    X = df.drop(columns=[target_col]).select_dtypes(include="number").fillna(0)
    if X.shape[1] == 0:
        return {"error": "No numeric feature columns left after excluding the target."}
    y = df[target_col].fillna(0)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    importances = dict(zip(X.columns, model.feature_importances_.round(4)))
    top_features = dict(sorted(importances.items(), key=lambda x: -x[1])[:10])

    return {
        "mae":          round(float(mean_absolute_error(y_test, y_pred)), 4),
        "r2":           round(float(r2_score(y_test, y_pred)), 4),
        "top_features": top_features,
    }
