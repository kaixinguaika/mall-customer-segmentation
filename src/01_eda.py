"""01 - Exploratory data analysis on the Mall Customer Segmentation dataset.

Outputs: figures/fig1_overview.png ... fig4_gender_profile.png
         results/descriptive_stats.csv, results/data_quality.json
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import load_data, set_style, save, dump, GENDER_COLORS, RES

set_style()
df = load_data()

# ---------------------------------------------------------------- data quality
quality = {
    "n_rows": int(len(df)),
    "n_cols": int(df.shape[1]),
    "columns": list(df.columns),
    "missing_values": {c: int(v) for c, v in df.isna().sum().items()},
    "duplicated_rows": int(df.duplicated().sum()),
    "duplicated_ids": int(df["CustomerID"].duplicated().sum()),
    "dtypes": {c: str(t) for c, t in df.dtypes.items()},
    "value_ranges": {
        "Age": [int(df.Age.min()), int(df.Age.max())],
        "Income": [float(df.Income.min()), float(df.Income.max())],
        "Spending": [int(df.Spending.min()), int(df.Spending.max())],
    },
    "gender_counts": {k: int(v) for k, v in df.Gender.value_counts().items()},
}
dump(quality, "data_quality.json")

# --------------------------------------------------------- descriptive summary
num = df[["Age", "Income", "Spending"]]
stats = num.describe().T
stats["skew"] = num.skew()
stats["kurtosis"] = num.kurt()
stats = stats[["count", "mean", "std", "min", "25%", "50%", "75%", "max", "skew", "kurtosis"]]
stats.round(2).to_csv(RES / "descriptive_stats.csv")
print(stats.round(2).to_string())

by_gender = df.groupby("Gender")[["Age", "Income", "Spending"]].agg(["mean", "std"]).round(2)
by_gender.to_csv(RES / "stats_by_gender.csv")
print("\n", by_gender.to_string())

corr = df[["Age", "Income", "Spending"]].corr()
corr.round(3).to_csv(RES / "correlation.csv")
print("\nPearson correlation\n", corr.round(3).to_string())

# ------------------------------------------------------------------- figure 1
fig, axes = plt.subplots(2, 2, figsize=(3.45, 3.6))
ax = axes[0, 0]
ax.hist(df.Age, bins=14, color="#3B6EA5", alpha=0.85, edgecolor="white", linewidth=0.5)
ax.set_xlabel("Age (years)")
ax.set_ylabel("Count")
ax.set_title("(a) Age distribution", pad=2)

ax = axes[0, 1]
ax.hist(df.Income, bins=14, color="#4E9A51", alpha=0.85, edgecolor="white", linewidth=0.5)
ax.set_xlabel("Annual income (k$)")
ax.set_ylabel("Count")
ax.set_title("(b) Annual income distribution")

ax = axes[1, 0]
ax.hist(df.Spending, bins=14, color="#E08A3C", alpha=0.85, edgecolor="white", linewidth=0.5)
ax.set_xlabel("Spending score (1-100)")
ax.set_ylabel("Count")
ax.set_title("(c) Spending score distribution")

ax = axes[1, 1]
counts = df.Gender.value_counts()
ax.bar(counts.index, counts.values, color=[GENDER_COLORS[g] for g in counts.index], width=0.55)
for i, v in enumerate(counts.values):
    ax.text(i, v + 2, f"{v} ({v / len(df):.0%})", ha="center", fontsize=7)
ax.set_ylabel("Count")
ax.set_ylim(0, counts.max() * 1.25)
ax.set_title("(d) Gender composition")
fig.tight_layout()
save(fig, "fig1_overview.png")

# ------------------------------------------------------------------- figure 2
fig, ax = plt.subplots(figsize=(3.4, 2.9))
for g in ["Female", "Male"]:
    sub = df[df.Gender == g]
    ax.scatter(sub.Income, sub.Spending, s=16, alpha=0.8, c=GENDER_COLORS[g],
               edgecolor="white", linewidth=0.4, label=f"{g} (n={len(sub)})")
ax.set_xlabel("Annual income (k$)")
ax.set_ylabel("Spending score (1-100)")
ax.legend(frameon=False, loc="upper right")
save(fig, "fig2_income_vs_spending.png")

# ------------------------------------------------------------------- figure 3
fig, ax = plt.subplots(figsize=(3.2, 2.8))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(3), corr.columns, rotation=30, ha="right")
ax.set_yticks(range(3), corr.index)
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=8,
                color="white" if abs(corr.values[i, j]) > 0.55 else "black")
ax.spines[:].set_visible(False)
fig.colorbar(im, ax=ax, shrink=0.8, pad=0.03).ax.tick_params(labelsize=6)
save(fig, "fig3_correlation.png")

# ------------------------------------------------------------------- figure 4
fig, axes = plt.subplots(1, 3, figsize=(6.8, 2.2))
for ax, col in zip(axes, ["Age", "Income", "Spending"]):
    data = [df.loc[df.Gender == g, col] for g in ["Female", "Male"]]
    bp = ax.boxplot(data, widths=0.5, patch_artist=True, medianprops=dict(color="black", lw=1))
    for patch, g in zip(bp["boxes"], ["Female", "Male"]):
        patch.set_facecolor(GENDER_COLORS[g])
        patch.set_alpha(0.75)
        patch.set_edgecolor("black")
        patch.set_linewidth(0.7)
    ax.set_xticks([1, 2], ["Female", "Male"])
    ax.set_ylabel(col if col != "Income" else "Annual income (k$)")
fig.tight_layout()
save(fig, "fig4_by_gender.png")

# ----------------------------------------------------- gender mean difference
from scipy import stats as st

tests = {}
for col in ["Age", "Income", "Spending"]:
    f = df.loc[df.Gender == "Female", col]
    m = df.loc[df.Gender == "Male", col]
    t, p = st.ttest_ind(f, m, equal_var=False)
    u, pu = st.mannwhitneyu(f, m)
    tests[col] = {"female_mean": round(float(f.mean()), 2), "male_mean": round(float(m.mean()), 2),
                  "t": round(float(t), 3), "p_welch": round(float(p), 4),
                  "mannwhitney_p": round(float(pu), 4)}
dump(tests, "gender_tests.json")
print("\nGender difference tests\n", pd.DataFrame(tests).T.to_string())
