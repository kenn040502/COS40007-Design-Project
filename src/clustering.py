"""
Clustering module.

Applies K-Means and Hierarchical (Ward) clustering to 16 Malaysian states
using CPI and income features derived from preprocessing.

Features used:
  mean_cpi_index       - average overall CPI index level
  cpi_growth_rate      - % CPI growth from earliest to latest month
  cpi_volatility       - std dev of monthly CPI (price stability proxy)
  income_mean_latest   - most recent survey mean household income
  income_median_latest - most recent survey median household income
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from scipy.cluster.hierarchy import dendrogram, linkage

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "figures")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "models")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURE_COLS = [
    "mean_cpi_index",
    "cpi_growth_rate",
    "cpi_volatility",
    "income_mean_latest",
    "income_median_latest",
]
MAX_K = 8   # 16 states → max sensible k is ~half the sample size


def prepare_features(df: pd.DataFrame):
    X = df[FEATURE_COLS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, scaler


def elbow_and_silhouette(X_scaled: np.ndarray) -> dict:
    inertias, silhouettes, db_scores, ch_scores = [], [], [], []
    k_range = range(2, MAX_K + 1)

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))
        db_scores.append(davies_bouldin_score(X_scaled, labels))
        ch_scores.append(calinski_harabasz_score(X_scaled, labels))

    best_k = list(k_range)[np.argmax(silhouettes)]
    return {
        "k_range": list(k_range),
        "inertias": inertias,
        "silhouettes": silhouettes,
        "db_scores": db_scores,
        "ch_scores": ch_scores,
        "best_k": best_k,
    }


def fit_kmeans(X_scaled: np.ndarray, k: int):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    return km, labels


def fit_hierarchical(X_scaled: np.ndarray, k: int):
    hc = AgglomerativeClustering(n_clusters=k, linkage="ward")
    labels = hc.fit_predict(X_scaled)
    return hc, labels


def pca_transform(X_scaled: np.ndarray):
    n_components = min(2, X_scaled.shape[1], X_scaled.shape[0])
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    return pca, X_pca


def assign_semantic_labels(df: pd.DataFrame, feature_cols=None) -> tuple:
    """
    Order clusters by mean income (ascending) and assign readable labels.
    """
    if feature_cols is None:
        feature_cols = FEATURE_COLS
    cluster_means = df.groupby("cluster")[feature_cols].mean()
    order = cluster_means["income_mean_latest"].argsort().values
    k = len(order)
    semantic = [
        "Low Income & Low CPI",
        "Mid-Low Income & Mid-Low CPI",
        "Mid-High Income & High CPI",
        "High Income & High CPI",
    ]
    label_map = {}
    for rank, orig_label in enumerate(order):
        label_map[orig_label] = semantic[rank] if rank < len(semantic) else f"Cluster {rank + 1}"
    df["cluster_label"] = df["cluster"].map(label_map)
    return df, label_map


def plot_elbow_silhouette(metrics: dict, save_path: str = None):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Optimal K Selection for State Clustering", fontsize=13, fontweight="bold")

    k_range = metrics["k_range"]
    best_k = metrics["best_k"]

    axes[0].plot(k_range, metrics["inertias"], "bo-")
    axes[0].axvline(x=best_k, color="red", linestyle="--", label=f"Best k={best_k}")
    axes[0].set_xlabel("Number of Clusters (k)")
    axes[0].set_ylabel("Inertia (WCSS)")
    axes[0].set_title("Elbow Method")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(k_range, metrics["silhouettes"], "go-")
    axes[1].axvline(x=best_k, color="red", linestyle="--", label=f"Best k={best_k}")
    axes[1].set_xlabel("Number of Clusters (k)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].set_title("Silhouette Analysis")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(k_range, metrics["db_scores"], "rs-")
    axes[2].axvline(x=best_k, color="red", linestyle="--", label=f"Best k={best_k}")
    axes[2].set_xlabel("Number of Clusters (k)")
    axes[2].set_ylabel("Davies-Bouldin (lower=better)")
    axes[2].set_title("Davies-Bouldin Index")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_clusters_pca(df_clustered: pd.DataFrame, X_pca: np.ndarray, pca: PCA,
                      title: str = "State Clusters (PCA)", save_path: str = None):
    fig, ax = plt.subplots(figsize=(10, 7))
    labels = sorted(df_clustered["cluster_label"].unique())
    palette = sns.color_palette("tab10", len(labels))
    color_map = dict(zip(labels, palette))

    for label in labels:
        mask = df_clustered["cluster_label"] == label
        ax.scatter(
            X_pca[mask, 0], X_pca[mask, 1],
            c=[color_map[label]], label=label, s=120,
            alpha=0.85, edgecolors="white", linewidths=0.6,
        )
        # Annotate each point with state name
        for idx in df_clustered[mask].index:
            pos = df_clustered.index.get_loc(idx)
            state = df_clustered.loc[idx, "state"]
            ax.annotate(state, (X_pca[pos, 0], X_pca[pos, 1]),
                        fontsize=7, ha="center", va="bottom",
                        xytext=(0, 6), textcoords="offset points")

    var = pca.explained_variance_ratio_
    ax.set_xlabel(f"PC1 ({var[0]*100:.1f}% variance)", fontsize=11)
    ax.set_ylabel(f"PC2 ({var[1]*100:.1f}% variance)" if len(var) > 1 else "PC2", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_cluster_profiles(df_clustered: pd.DataFrame, save_path: str = None):
    """Heatmap of normalised feature means per cluster + state count bar chart."""
    profile = df_clustered.groupby("cluster_label")[FEATURE_COLS].mean().reset_index()

    norm_profile = profile.copy()
    for col in FEATURE_COLS:
        col_min = norm_profile[col].min()
        col_max = norm_profile[col].max()
        norm_profile[col] = (norm_profile[col] - col_min) / (col_max - col_min + 1e-9)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("State Cluster Socioeconomic Profiles", fontsize=13, fontweight="bold")

    heat_data = norm_profile.set_index("cluster_label")[FEATURE_COLS]
    annot_data = profile.set_index("cluster_label")[FEATURE_COLS].round(2)
    sns.heatmap(
        heat_data, annot=annot_data, fmt=".2f", cmap="RdYlGn", ax=axes[0],
        linewidths=0.5, cbar_kws={"label": "Normalised value"},
    )
    axes[0].set_title("Feature Means per Cluster (normalised colour)")
    axes[0].set_xlabel("")

    counts = df_clustered["cluster_label"].value_counts().reset_index()
    counts.columns = ["cluster_label", "count"]
    axes[1].bar(counts["cluster_label"], counts["count"],
                color=sns.color_palette("tab10", len(counts)))
    axes[1].set_xlabel("Cluster")
    axes[1].set_ylabel("Number of States")
    axes[1].set_title("State Count per Cluster")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_dendrogram(X_scaled: np.ndarray, labels: list = None, save_path: str = None):
    Z = linkage(X_scaled, method="ward")
    fig, ax = plt.subplots(figsize=(12, 5))
    dendrogram(Z, labels=labels, ax=ax, leaf_rotation=45, leaf_font_size=9,
               color_threshold=0.7 * max(Z[:, 2]))
    ax.set_title("Hierarchical Clustering Dendrogram — Malaysian States (Ward Linkage)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("State")
    ax.set_ylabel("Distance")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def run_all(state_features_df: pd.DataFrame = None) -> dict:
    if state_features_df is None:
        state_features_df = pd.read_csv(os.path.join(PROCESSED_DIR, "state_features.csv"))

    print("Running clustering analysis on Malaysian states...")
    X_scaled, scaler = prepare_features(state_features_df)

    metrics = elbow_and_silhouette(X_scaled)
    best_k = metrics["best_k"]
    print(f"  Elbow/Silhouette -> best k = {best_k}")

    plot_elbow_silhouette(metrics, save_path=os.path.join(FIGURES_DIR, "cluster_elbow_silhouette.png"))

    # K-Means
    _, km_labels = fit_kmeans(X_scaled, best_k)
    pca, X_pca = pca_transform(X_scaled)

    df_km = state_features_df[["state"] + FEATURE_COLS].copy()
    df_km["cluster"] = km_labels
    # PCA coordinates (row order matches X_scaled / state_features_df) so the
    # dashboard can render an interactive scatter instead of a static PNG.
    df_km["pc1"] = X_pca[:, 0]
    df_km["pc2"] = X_pca[:, 1] if X_pca.shape[1] > 1 else 0.0
    df_km, label_map_km = assign_semantic_labels(df_km)

    km_scores = {
        "silhouette": round(silhouette_score(X_scaled, km_labels), 4),
        "davies_bouldin": round(davies_bouldin_score(X_scaled, km_labels), 4),
        "calinski_harabasz": round(calinski_harabasz_score(X_scaled, km_labels), 4),
        "k": best_k,
    }
    print(f"  K-Means scores: {km_scores}")

    plot_clusters_pca(df_km, X_pca, pca, title="K-Means State Clusters (PCA)",
                      save_path=os.path.join(FIGURES_DIR, "cluster_pca_kmeans.png"))
    plot_cluster_profiles(df_km, save_path=os.path.join(FIGURES_DIR, "cluster_profiles.png"))

    # Hierarchical
    _, hc_labels = fit_hierarchical(X_scaled, best_k)
    df_hc = state_features_df[["state"] + FEATURE_COLS].copy()
    df_hc["cluster"] = hc_labels
    df_hc["pc1"] = X_pca[:, 0]
    df_hc["pc2"] = X_pca[:, 1] if X_pca.shape[1] > 1 else 0.0
    df_hc, label_map_hc = assign_semantic_labels(df_hc)

    hc_scores = {
        "silhouette": round(silhouette_score(X_scaled, hc_labels), 4),
        "davies_bouldin": round(davies_bouldin_score(X_scaled, hc_labels), 4),
        "calinski_harabasz": round(calinski_harabasz_score(X_scaled, hc_labels), 4),
        "k": best_k,
    }
    print(f"  Hierarchical scores: {hc_scores}")

    plot_clusters_pca(df_hc, X_pca, pca, title="Hierarchical Clustering — States (PCA)",
                      save_path=os.path.join(FIGURES_DIR, "cluster_pca_hierarchical.png"))
    plot_dendrogram(X_scaled, labels=state_features_df["state"].tolist(),
                    save_path=os.path.join(FIGURES_DIR, "cluster_dendrogram.png"))

    # Export the dendrogram's drawable coordinates (no_plot) so the dashboard
    # can render an interactive, hoverable version instead of a static PNG.
    Z = linkage(X_scaled, method="ward")
    dn = dendrogram(Z, labels=state_features_df["state"].tolist(),
                    color_threshold=0.7 * max(Z[:, 2]), no_plot=True)
    dendro_data = {
        "icoord": dn["icoord"],          # x-coordinates of each link (U shape)
        "dcoord": dn["dcoord"],          # heights of each link
        "ivl": dn["ivl"],                # leaf labels, left → right
        "color_list": dn["color_list"],  # matplotlib colour code per link
    }

    df_km.to_csv(os.path.join(PROCESSED_DIR, "states_kmeans_clustered.csv"), index=False)
    df_hc.to_csv(os.path.join(PROCESSED_DIR, "states_hierarchical_clustered.csv"), index=False)

    result = {
        "best_k": best_k,
        "elbow_metrics": metrics,
        "pca_variance": [float(v) for v in pca.explained_variance_ratio_],
        "feature_cols": FEATURE_COLS,
        "dendrogram": dendro_data,
        "kmeans": {
            "scores": km_scores,
            "label_map": {int(k): v for k, v in label_map_km.items()},
        },
        "hierarchical": {
            "scores": hc_scores,
            "label_map": {int(k): v for k, v in label_map_hc.items()},
        },
        "df_kmeans": df_km,
        "df_hierarchical": df_hc,
    }

    with open(os.path.join(MODELS_DIR, "clustering_results.json"), "w") as f:
        json.dump(
            {k: v for k, v in result.items() if k not in ("df_kmeans", "df_hierarchical")},
            f, indent=2,
        )

    print("  Clustering complete. Figures and results saved.")
    return result


if __name__ == "__main__":
    run_all()
