"""02 - Customer segmentation with K-Means (k selection, validation, profiling).

Main feature space: standardized Annual Income + Spending Score.
Outputs: figures/fig5_k_selection.png, fig6_clusters.png, fig7_algorithm_comparison.png,
         fig8_three_features.png
         results/cluster_profiles.csv, segments.csv, clustering_metrics.json
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN, BisectingKMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (silhouette_score, davies_bouldin_score,
                             calinski_harabasz_score, adjusted_rand_score)
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import PCA

from common import load_data, set_style, save, dump, RES, FIG, PALETTE

set_style()
RNG = 42
df = load_data()

X = df[["Income", "Spending"]].values
Xs = StandardScaler().fit_transform(X)

# ------------------------------------------------------- 1. choose k (elbow + silhouette)
ks = list(range(1, 11))
inertia, sil, db, ch = {}, {}, {}, {}
for k in ks:
    km = KMeans(n_clusters=k, n_init=50, random_state=RNG).fit(Xs)
    inertia[k] = float(km.inertia_)
    if k >= 2:
        lab = km.labels_
        sil[k] = float(silhouette_score(Xs, lab))
        db[k] = float(davies_bouldin_score(Xs, lab))
        ch[k] = float(calinski_harabasz_score(Xs, lab))

sil_df = pd.DataFrame({"k": list(sil.keys()),
                       "sse": [round(inertia[k], 1) for k in sil.keys()],
                       "silhouette": list(sil.values()),
                       "davies_bouldin": list(db.values()),
                       "calinski_harabasz": list(ch.values())}).round(4)
sil_df.to_csv(RES / "k_selection.csv", index=False)
print(sil_df.to_string(index=False))

best_k = int(max(sil, key=sil.get))
K = 5  # elbow + interpretability + literature convention for this dataset
print(f"\nSilhouette-optimal k = {best_k}; working k = {K}")

# ------------------------------------------------------- 2. final K-Means model
km = KMeans(n_clusters=K, n_init=100, random_state=RNG).fit(Xs)
labels = km.labels_
centers = StandardScaler().fit(X).inverse_transform(km.cluster_centers_)

metrics = {
    "k": K,
    "silhouette": round(float(silhouette_score(Xs, labels)), 4),
    "davies_bouldin": round(float(davies_bouldin_score(Xs, labels)), 4),
    "calinski_harabasz": round(float(calinski_harabasz_score(Xs, labels)), 2),
    "inertia": round(float(km.inertia_), 2),
    "n_iter": int(km.n_iter_),
    "silhouette_optimal_k": best_k,
}

# ------------------------------------------------------------- 3. algorithm comparison
algos = {}
algos["K-Means (k=5)"] = labels
algos["Bisecting K-Means"] = BisectingKMeans(n_clusters=K, n_init=20, random_state=RNG).fit_predict(Xs)
algos["Agglomerative (Ward)"] = AgglomerativeClustering(n_clusters=K, linkage="ward").fit_predict(Xs)
algos["Gaussian Mixture"] = GaussianMixture(n_components=K, covariance_type="full",
                                            n_init=10, random_state=RNG).fit_predict(Xs)

# DBSCAN: eps from the knee region of the 5-NN distance curve
nn = NearestNeighbors(n_neighbors=5).fit(Xs)
dist, _ = nn.kneighbors(Xs)
eps = float(np.percentile(dist[:, -1], 90))
algos[f"DBSCAN (eps={eps:.2f})"] = DBSCAN(eps=eps, min_samples=5).fit_predict(Xs)

comp = []
for name, lab in algos.items():
    n_clusters = len(set(lab) - {-1})
    noise = int((lab == -1).sum())
    row = {"algorithm": name, "n_clusters": n_clusters, "noise_points": noise,
           "ARI_vs_kmeans": round(float(adjusted_rand_score(labels, lab)), 4)}
    if n_clusters >= 2 and noise < len(lab) * 0.5:
        mask = lab != -1
        row["silhouette"] = round(float(silhouette_score(Xs[mask], lab[mask])), 4)
    comp.append(row)
comp_df = pd.DataFrame(comp)
comp_df.to_csv(RES / "algorithm_comparison.csv", index=False)
print("\n", comp_df.to_string(index=False))

# stability: 30 bootstrap resamples, ARI against the reference partition
rng = np.random.default_rng(RNG)
aris = []
for _ in range(30):
    idx = rng.choice(len(Xs), size=len(Xs), replace=True)
    lab_b = KMeans(n_clusters=K, n_init=10, random_state=RNG).fit_predict(Xs[idx])
    aris.append(adjusted_rand_score(labels[idx], lab_b))
metrics["bootstrap_ARI_mean"] = round(float(np.mean(aris)), 4)
metrics["bootstrap_ARI_std"] = round(float(np.std(aris)), 4)
print(f"\nStability ARI = {np.mean(aris):.3f} +/- {np.std(aris):.3f}")

# ------------------------------------------- 4. compare with 3-feature solution
X3 = StandardScaler().fit_transform(df[["Age", "Income", "Spending"]].values)
km3 = KMeans(n_clusters=K, n_init=50, random_state=RNG).fit(X3)
metrics["three_feature_silhouette"] = round(float(silhouette_score(X3, km3.labels_)), 4)
metrics["two_feature_silhouette"] = metrics["silhouette"]

# --------------------------------------------------------------- 5. profiling
df["Cluster"] = labels
prof = df.groupby("Cluster").agg(
    n=("CustomerID", "size"),
    age_mean=("Age", "mean"),
    age_std=("Age", "std"),
    income_mean=("Income", "mean"),
    income_std=("Income", "std"),
    spending_mean=("Spending", "mean"),
    spending_std=("Spending", "std"),
    female_share=("Gender", lambda s: (s == "Female").mean()),
    mean_customer_value=("Spending", lambda s: s.mean()),
).round(2)
prof["share"] = (prof["n"] / len(df)).round(3)


def name_segment(inc, spd, inc_mid, spd_mid):
    hi_i, hi_s = inc > inc_mid, spd > spd_mid
    if hi_i and hi_s:
        return "Target (affluent, high spend)"
    if hi_i and not hi_s:
        return "Conservative (affluent, low spend)"
    if not hi_i and hi_s:
        return "Impulsive (low income, high spend)"
    return "Frugal (low income, low spend)"


inc_mid = float(df.Income.median())
spd_mid = float(df.Spending.median())
prof["segment"] = [name_segment(r.income_mean, r.spending_mean, inc_mid, spd_mid)
                   for r in prof.itertuples()]
# the cluster sitting near the centre of both axes is the "standard" group
centre = (prof.income_mean - inc_mid).abs() + (prof.spending_mean - spd_mid).abs()
prof.loc[centre.idxmin(), "segment"] = "Standard (average income & spend)"
prof = prof.sort_values("income_mean")
print("\n", prof.to_string())

prof.to_csv(RES / "cluster_profiles.csv")

# stable, human-readable cluster ids ordered by income then spending
_ord = prof.reset_index().assign(ib=lambda d: (d.income_mean / 10).round())
order = _ord.sort_values(["ib", "spending_mean"]).Cluster.tolist()
remap = {old: new for new, old in enumerate(order)}
seg_names = {new: prof.loc[prof.index == old, "segment"].iloc[0] for old, new in remap.items()}
df["Segment"] = df.Cluster.map(remap)
df["SegmentName"] = df.Segment.map(seg_names)

out = df.copy()
out["Segment"] = out.apply(lambda r: f"C{r.Segment}: {r.SegmentName}", axis=1)
out[["CustomerID", "Gender", "Age", "Income", "Spending", "Segment"]].to_csv(
    RES / "segments.csv", index=False)

metrics["segments"] = {f"C{k}: {v}": int((df.Segment == k).sum()) for k, v in seg_names.items()}
centers_df = pd.DataFrame(centers, columns=["Income", "Spending"]).sort_values(["Income", "Spending"])
centers_df.round(2).to_csv(RES / "cluster_centers.csv", index=False)
dump(metrics, "clustering_metrics.json")
print("\n", {k: v for k, v in metrics.items() if k != "segments"})

# ------------------------------------------------------------------ figure 5
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.5))
ax = axes[0]
ax.plot(list(inertia.keys()), list(inertia.values()), marker="o", ms=3.5, color="#3B6EA5")
ax.axvline(K, ls="--", lw=0.8, color="#C0504D")
ax.set_xlabel("Number of clusters k")
ax.set_ylabel("Within-cluster SSE")
ax.set_title("(a) Elbow method")

ax = axes[1]
ax.plot(list(sil.keys()), list(sil.values()), marker="o", ms=3.5, color="#4E9A51")
ax.axvline(K, ls="--", lw=0.8, color="#C0504D")
ax.annotate(f"k={K}\nsil={sil[K]:.3f}", xy=(K, sil[K]), xytext=(K + 0.4, min(sil.values()) + 0.02),
            fontsize=7, color="#C0504D",
            arrowprops=dict(arrowstyle="->", lw=0.7, color="#C0504D"))
ax.set_xlabel("Number of clusters k")
ax.set_ylabel("Mean silhouette coefficient")
ax.set_title("(b) Silhouette analysis")
fig.tight_layout()
save(fig, "fig5_k_selection.png")

# ------------------------------------------------------------------ figure 6
fig, ax = plt.subplots(figsize=(3.35, 3.45))
for k in sorted(df.Segment.unique()):
    sub = df[df.Segment == k]
    ax.scatter(sub.Income, sub.Spending, s=13, alpha=0.85, color=PALETTE[k % len(PALETTE)],
               edgecolor="white", linewidth=0.4,
               label=f"C{k} (n={len(sub)}): {seg_names[k]}")
c = pd.DataFrame(centers, columns=["Income", "Spending"])
for k in sorted(df.Segment.unique()):
    pt = c.iloc[k]
    ax.scatter(pt.Income, pt.Spending, marker="X", s=70, c="black", edgecolor="white", linewidth=0.8, zorder=5)
ax.set_xlabel("Annual income (k$)")
ax.set_ylabel("Spending score (1-100)")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.155), ncol=1, fontsize=6, handletextpad=0.2, labelspacing=0.3)
save(fig, "fig6_clusters.png")

# ------------------------------------------------------------------ figure 7
fig, ax = plt.subplots(figsize=(3.6, 2.4))
names = comp_df.algorithm.tolist()
vals = comp_df.ARI_vs_kmeans.tolist()
bars = ax.barh(range(len(names)), vals, color=["#3B6EA5"] + ["#9DB4CE"] * (len(names) - 1), height=0.6)
ax.set_yticks(range(len(names)), [n.split(" (")[0] for n in names], fontsize=7)
ax.set_xlim(0, 1.12)
ax.set_xlabel("Adjusted Rand index vs. K-Means partition")
for i, v in enumerate(vals):
    ax.text(v + 0.02, i, f"{v:.2f}", va="center", fontsize=7)
ax.invert_yaxis()
save(fig, "fig7_algorithm_comparison.png")

# ------------------------------------------------------------------ figure 8
pca = PCA(n_components=2, random_state=RNG).fit(X3)
P = pca.transform(X3)
fig, ax = plt.subplots(figsize=(3.6, 2.9))
for k in sorted(set(km3.labels_)):
    m = km3.labels_ == k
    ax.scatter(P[m, 0], P[m, 1], s=14, alpha=0.8, color=PALETTE[k % len(PALETTE)],
               edgecolor="white", linewidth=0.3, label=f"C{k}")
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.0%} var.)")
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.0%} var.)")
ax.legend(frameon=False, ncol=5, fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.2))
save(fig, "fig8_three_features.png")

dump({"pca_explained": [round(float(v), 3) for v in pca.explained_variance_ratio_],
      "km3_labels": np.bincount(km3.labels_).tolist()}, "three_feature_pca.json")

# ------------------------------------------------- appendix figure: signature
fig, axes = plt.subplots(3, 1, figsize=(3.3, 4.0))
metrics_cols = [("Age", "Age (years)"), ("Income", "Annual income (k$)"), ("Spending", "Spending score")]
labels = [f"C{k}" for k in sorted(df.Segment.unique())]
for ax, (col, lab) in zip(axes, metrics_cols):
    means = [df.loc[df.Segment == k, col].mean() for k in sorted(df.Segment.unique())]
    bars = ax.bar(labels, means, color=[PALETTE[k % len(PALETTE)] for k in sorted(df.Segment.unique())],
                  width=0.68, edgecolor="white", linewidth=0.5)
    for b, v in zip(bars, means):
        ax.text(b.get_x() + b.get_width() / 2, v + max(means) * 0.02, f"{v:.0f}",
                ha="center", fontsize=6.5)
    ax.set_title(lab, pad=2, loc="left", fontsize=8)
    ax.set_ylim(0, max(means) * 1.16)
    ax.tick_params(axis="x", labelsize=7)
fig.tight_layout()
save(fig, "fig13_segment_signature.png")
