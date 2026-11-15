"""Regenerate the two wide figures at single-column width for the Word version."""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "docx_assets"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
    "axes.grid": False, "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": 0.7, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

df = pd.read_csv(ROOT / "Mall_Customers.csv").rename(
    columns={"Annual Income (k$)": "Income", "Spending Score (1-100)": "Spending"})
COLORS = {"Male": "#3B6EA5", "Female": "#C0504D"}

# ---- figure 4 : boxplots by gender, single column -------------------------
fig, axes = plt.subplots(3, 1, figsize=(3.45, 4.4))
for ax, col in zip(axes, ["Age", "Income", "Spending"]):
    data = [df.loc[df.Gender == g, col] for g in ["Female", "Male"]]
    bp = ax.boxplot(data, widths=0.45, patch_artist=True, medianprops=dict(color="black", lw=0.9))
    for patch, g in zip(bp["boxes"], ["Female", "Male"]):
        patch.set_facecolor(COLORS[g]); patch.set_alpha(0.75)
        patch.set_edgecolor("black"); patch.set_linewidth(0.6)
    ax.set_xticks([1, 2], ["Female", "Male"])
    ax.set_ylabel({"Age": "Age (years)", "Income": "Annual income (k$)", "Spending": "Spending score"}[col])
fig.tight_layout(h_pad=0.8)
fig.savefig(OUT / "fig4_docx.png")
plt.close(fig)

# ---- figure 5 : elbow + silhouette, stacked ------------------------------
X = df[["Income", "Spending"]].values
Xs = StandardScaler().fit_transform(X)
ks, inertia, sil = list(range(1, 11)), {}, {}
for k in ks:
    km = KMeans(n_clusters=k, n_init=50, random_state=42).fit(Xs)
    inertia[k] = km.inertia_
    if k >= 2:
        sil[k] = silhouette_score(Xs, km.labels_)

fig, axes = plt.subplots(2, 1, figsize=(3.45, 4.0))
ax = axes[0]
ax.plot(list(inertia), list(inertia.values()), marker="o", ms=2.5, color="#3B6EA5", lw=1)
ax.axvline(5, ls="--", lw=0.7, color="#C0504D")
ax.set_xlabel("Number of clusters k"); ax.set_ylabel("Within-cluster SSE")
ax.set_title("(a) Elbow method", pad=2)

ax = axes[1]
ax.plot(list(sil), list(sil.values()), marker="o", ms=2.5, color="#4E9A51", lw=1)
ax.axvline(5, ls="--", lw=0.7, color="#C0504D")
ax.annotate(f"k=5, sil={sil[5]:.3f}", xy=(5, sil[5]), xytext=(5.6, 0.34), fontsize=6.2,
            color="#C0504D", arrowprops=dict(arrowstyle="->", lw=0.6, color="#C0504D"))
ax.set_xlabel("Number of clusters k"); ax.set_ylabel("Mean silhouette")
ax.set_title("(b) Silhouette analysis", pad=2)
fig.tight_layout(h_pad=1.0)
fig.savefig(OUT / "fig5_docx.png")
plt.close(fig)

print("saved", sorted(p.name for p in OUT.glob("*.png")))
