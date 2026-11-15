"""03 - Supervised classification of the discovered segments.

Purpose: turn the unsupervised segmentation into a rule that can label a *new*
customer at the till (Gender + Age + Income + Spending -> segment).

Outputs: figures/fig9_model_comparison.png, fig10_confusion.png,
         fig11_feature_importance.png, fig12_decision_boundary.png
         results/classification_cv.csv, classification_report.json
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix,
                             classification_report)

from common import set_style, save, dump, RES, PALETTE

set_style()
RNG = 42

seg = pd.read_csv(RES / "segments.csv")
seg["y"] = seg["Segment"].str.extract(r"C(\d)").astype(int)
seg["GenderBin"] = (seg.Gender == "Male").astype(int)

FEATS = ["GenderBin", "Age", "Income", "Spending"]
X = seg[FEATS].values
y = seg["y"].values

models = {
    "Logistic regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, random_state=RNG)),
    "k-NN (k=5)": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5)),
    "SVM (RBF)": make_pipeline(StandardScaler(), SVC(kernel="rbf", C=3.0, gamma="scale", random_state=RNG)),
    "Decision tree": DecisionTreeClassifier(max_depth=4, random_state=RNG),
    "Random forest": RandomForestClassifier(n_estimators=300, random_state=RNG),
    "Gradient boosting": GradientBoostingClassifier(random_state=RNG),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RNG)
rows = []
for name, mdl in models.items():
    r = cross_validate(mdl, X, y, cv=cv, scoring=["accuracy", "f1_macro"], n_jobs=1)
    rows.append({"model": name,
                 "cv_accuracy": round(r["test_accuracy"].mean(), 4),
                 "cv_accuracy_std": round(r["test_accuracy"].std(), 4),
                 "cv_macro_f1": round(r["test_f1_macro"].mean(), 4),
                 "cv_macro_f1_std": round(r["test_f1_macro"].std(), 4)})
cv_df = pd.DataFrame(rows).sort_values("cv_macro_f1", ascending=False)
cv_df.to_csv(RES / "classification_cv.csv", index=False)
print(cv_df.to_string(index=False))

# --------------------------------------------------- hold-out evaluation (30%)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=RNG)
best_name = cv_df.iloc[0].model
best = models[best_name]
best.fit(Xtr, ytr)
pred = best.predict(Xte)

holdout = {
    "best_model": best_name,
    "test_accuracy": round(float(accuracy_score(yte, pred)), 4),
    "test_macro_f1": round(float(f1_score(yte, pred, average="macro")), 4),
    "n_train": int(len(ytr)),
    "n_test": int(len(yte)),
}
print("\nHold-out:", holdout)
print(classification_report(yte, pred, zero_division=0))

# ------------------------------------- demographics-only (honest generalisation)
Xd = seg[["GenderBin", "Age"]].values
rows_d = []
for name in ["Logistic regression", "Random forest"]:
    r = cross_validate(models[name], Xd, y, cv=cv, scoring=["accuracy", "f1_macro"], n_jobs=1)
    rows_d.append({"model": name, "cv_accuracy": round(r["test_accuracy"].mean(), 4),
                   "cv_macro_f1": round(r["test_f1_macro"].mean(), 4)})
demo_df = pd.DataFrame(rows_d)
print("\nDemographics only (Gender+Age):\n", demo_df.to_string(index=False))
demo_df.to_csv(RES / "classification_demographics_only.csv", index=False)

# ---------------------------------------------------------------- figure 9
fig, ax = plt.subplots(figsize=(3.9, 2.4))
d = cv_df.iloc[::-1]
ypos = np.arange(len(d))
ax.barh(ypos - 0.18, d.cv_accuracy, height=0.34, color="#3B6EA5", label="Accuracy")
ax.barh(ypos + 0.18, d.cv_macro_f1, height=0.34, color="#E08A3C", label="Macro F1")
ax.set_yticks(ypos, d.model, fontsize=7)
ax.set_xlim(0, 1.12)
ax.set_xlabel("5-fold cross-validated score")
ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.18))
save(fig, "fig9_model_comparison.png")

# ---------------------------------------------------------------- figure 10
cm = confusion_matrix(yte, pred)
fig, ax = plt.subplots(figsize=(2.9, 2.6))
im = ax.imshow(cm, cmap="Blues")
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8,
                color="white" if cm[i, j] > cm.max() / 2 else "black")
ax.set_xticks(range(5), [f"C{i}" for i in range(5)])
ax.set_yticks(range(5), [f"C{i}" for i in range(5)])
ax.set_xlabel("Predicted segment")
ax.set_ylabel("True segment")
ax.spines[:].set_visible(False)
save(fig, "fig10_confusion.png")

# ---------------------------------------------------------------- figure 11
rf = RandomForestClassifier(n_estimators=300, random_state=RNG).fit(X, y)
imp = rf.feature_importances_
fig, ax = plt.subplots(figsize=(3.0, 2.0))
order = np.argsort(imp)
ax.barh([["Gender", "Age", "Income", "Spending"][i] for i in order], imp[order],
        color="#4E9A51", height=0.55)
ax.set_xlabel("Impurity-based importance")
save(fig, "fig11_feature_importance.png")

# ---------------------------------------------------------------- figure 12
# decision surface in the (income, spending) plane, averaged over the dataset
xx, yy = np.meshgrid(np.linspace(10, 145, 300), np.linspace(-2, 102, 300))
grid = np.c_[np.full(xx.size, seg.GenderBin.mean()), np.full(xx.size, seg.Age.median()),
             xx.ravel(), yy.ravel()]
Z = rf.predict(grid).reshape(xx.shape)

fig, ax = plt.subplots(figsize=(4.0, 3.2))
from matplotlib.colors import ListedColormap
ax.contourf(xx, yy, Z, levels=np.arange(-0.5, 5.5, 1),
            colors=[PALETTE[i] for i in range(5)], alpha=0.22)
for k in range(5):
    m = y == k
    ax.scatter(seg.Income[m], seg.Spending[m], s=12, color=PALETTE[k], edgecolor="white",
               linewidth=0.3, label=f"C{k}")
ax.set_xlabel("Annual income (k$)")
ax.set_ylabel("Spending score (1-100)")
ax.legend(frameon=False, ncol=5, fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.18))
save(fig, "fig12_decision_boundary.png")

dump({"holdout": holdout,
      "feature_importance": {f: round(float(v), 4) for f, v in zip(["Gender", "Age", "Income", "Spending"], imp)},
      "best_cv": cv_df.iloc[0].to_dict(),
      "demographics_only": demo_df.to_dict("records")},
     "classification_report.json")
