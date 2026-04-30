"""
Clustering module.
Applies K-Means and Hierarchical clustering to 160 Malaysian districts
using HIES district-level features: income, expenditure, gini, poverty.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

FEATURE_COLS = ["income_mean", "income_median", "expenditure_mean", "gini", "poverty"]
CLUSTER_LABELS = {
    0: "High Income, Low Poverty",
    1: "Mid Income, Moderate Poverty",
    2: "Low Income, High Poverty",
    3: "High Inequality",
}
MAX_K = 10


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
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    return pca, X_pca


def assign_semantic_labels(df: pd.DataFrame, feature_cols=FEATURE_COLS) -> pd.DataFrame:
    """
    Order clusters by mean income (ascending) and relabel semantically.
    """
    cluster_means = df.groupby("cluster")[feature_cols].mean()
    order = cluster_means["income_mean"].argsort().values
    label_map = {}
    semantic = [
        "Low Income, High Poverty",
        "Mid-Low Income",
        "Mid-High Income",
        "High Income, Low Poverty",
    ]
    for rank, orig_label in enumerate(order):
        label_map[orig_label] = semantic[rank] if rank < len(semantic) else f"Cluster {rank}"
    df["cluster_label"] = df["cluster"].map(label_map)
    return df, label_map


def plot_elbow_silhouette(metrics: dict, save_path: str = None):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Optimal K Selection for K-Means Clustering", fontsize=13, fontweight="bold")

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
    axes[2].set_ylabel("Davies-Bouldin Score (lower=better)")
    axes[2].set_title("Davies-Bouldin Index")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_clusters_pca(df_clustered: pd.DataFrame, X_pca: np.ndarray, pca: PCA,
                      title: str = "District Clusters (PCA)", save_path: str = None):
    fig, ax = plt.subplots(figsize=(10, 7))
    labels = df_clustered["cluster_label"].unique()
    palette = sns.color_palette("tab10", len(labels))
    color_map = dict(zip(sorted(labels), palette))

    for label in sorted(labels):
        mask = df_clustered["cluster_label"] == label
        ax.scatter(
            X_pca[mask, 0], X_pca[mask, 1],
            c=[color_map[label]], label=label,
            s=60, alpha=0.75, edgecolors="white", linewidths=0.4,
        )

    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)", fontsize=11)
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_cluster_profiles(df_clustered: pd.DataFrame, save_path: str = None):
    """Radar/heatmap of mean feature values per cluster."""
    profile = df_clustered.groupby("cluster_label")[FEATURE_COLS].mean().reset_index()

    # Normalise for heatmap readability
    norm_profile = profile.copy()
    for col in FEATURE_COLS:
        col_min, col_max = norm_profile[col].min(), norm_profile[col].max()
        norm_profile[col] = (norm_profile[col] - col_min) / (col_max - col_min + 1e-9)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("District Cluster Socioeconomic Profiles", fontsize=13, fontweight="bold")

    # Heatmap
    heat_data = norm_profile.set_index("cluster_label")[FEATURE_COLS]
    sns.heatmap(
        heat_data, annot=profile.set_index("cluster_label")[FEATURE_COLS].round(1),
        fmt=".1f", cmap="RdYlGn_r", ax=axes[0], linewidths=0.5,
        cbar_kws={"label": "Normalised value"},
    )
    axes[0].set_title("Feature Means per Cluster (normalised colour)")
    axes[0].set_xlabel("")

    # Count per cluster
    counts = df_clustered["cluster_label"].value_counts().reset_index()
    counts.columns = ["cluster_label", "count"]
    axes[1].bar(counts["cluster_label"], counts["count"],
                color=sns.color_palette("tab10", len(counts)))
    axes[1].set_xlabel("Cluster")
    axes[1].set_ylabel("Number of Districts")
    axes[1].set_title("District Count per Cluster")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def plot_dendrogram(X_scaled: np.ndarray, labels: list = None, save_path: str = None):
    Z = linkage(X_scaled, method="ward")
    fig, ax = plt.subplots(figsize=(14, 5))
    dendrogram(Z, labels=labels, ax=ax, leaf_rotation=90, leaf_font_size=6,
               color_threshold=0.7 * max(Z[:, 2]))
    ax.set_title("Hierarchical Clustering Dendrogram (Ward Linkage)", fontsize=13, fontweight="bold")
    ax.set_xlabel("District")
    ax.set_ylabel("Distance")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close()
    return fig


def run_all(hies_district_df: pd.DataFrame = None) -> dict:
    if hies_district_df is None:
        hies_district_df = pd.read_csv(os.path.join(PROCESSED_DIR, "hies_district_clean.csv"))

    print("Running clustering analysis...")

    X_scaled, scaler = prepare_features(hies_district_df)

    # Determine best k
    metrics = elbow_and_silhouette(X_scaled)
    best_k = metrics["best_k"]
    print(f"  Elbow/Silhouette -> best k = {best_k}")

    plot_elbow_silhouette(metrics, save_path=os.path.join(FIGURES_DIR, "cluster_elbow_silhouette.png"))

    # K-Means
    km_model, km_labels = fit_kmeans(X_scaled, best_k)
    pca, X_pca = pca_transform(X_scaled)

    df_km = hies_district_df[["state", "district"] + FEATURE_COLS].copy()
    df_km["cluster"] = km_labels
    df_km, label_map_km = assign_semantic_labels(df_km)

    km_scores = {
        "silhouette": round(silhouette_score(X_scaled, km_labels), 4),
        "davies_bouldin": round(davies_bouldin_score(X_scaled, km_labels), 4),
        "calinski_harabasz": round(calinski_harabasz_score(X_scaled, km_labels), 4),
        "k": best_k,
    }
    print(f"  K-Means scores: {km_scores}")

    plot_clusters_pca(df_km, X_pca, pca, title="K-Means District Clusters (PCA)",
                      save_path=os.path.join(FIGURES_DIR, "cluster_pca_kmeans.png"))
    plot_cluster_profiles(df_km, save_path=os.path.join(FIGURES_DIR, "cluster_profiles.png"))

    # Hierarchical
    _, hc_labels = fit_hierarchical(X_scaled, best_k)
    df_hc = hies_district_df[["state", "district"] + FEATURE_COLS].copy()
    df_hc["cluster"] = hc_labels
    df_hc, label_map_hc = assign_semantic_labels(df_hc)

    hc_scores = {
        "silhouette": round(silhouette_score(X_scaled, hc_labels), 4),
        "davies_bouldin": round(davies_bouldin_score(X_scaled, hc_labels), 4),
        "calinski_harabasz": round(calinski_harabasz_score(X_scaled, hc_labels), 4),
        "k": best_k,
    }
    print(f"  Hierarchical scores: {hc_scores}")

    plot_clusters_pca(df_hc, X_pca, pca, title="Hierarchical Clustering (PCA)",
                      save_path=os.path.join(FIGURES_DIR, "cluster_pca_hierarchical.png"))
    plot_dendrogram(X_scaled, labels=hies_district_df["district"].tolist(),
                    save_path=os.path.join(FIGURES_DIR, "cluster_dendrogram.png"))

    # Save clustered data
    df_km.to_csv(os.path.join(PROCESSED_DIR, "districts_kmeans_clustered.csv"), index=False)
    df_hc.to_csv(os.path.join(PROCESSED_DIR, "districts_hierarchical_clustered.csv"), index=False)

    result = {
        "best_k": best_k,
        "elbow_metrics": metrics,
        "kmeans": {"scores": km_scores, "label_map": {int(k): v for k, v in label_map_km.items()}},
        "hierarchical": {"scores": hc_scores, "label_map": {int(k): v for k, v in label_map_hc.items()}},
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
