# Mall Customer Segmentation

Customer segmentation of 200 mall shoppers using **K-Means** (unsupervised) and **supervised classification** of the discovered segments, written for the *Machine Learning (Fall 2026)* course project.

The study asks two questions: **how many behaviourally distinct shopper groups exist**, and **can a new customer be assigned to one of them automatically** at the point of sale?

---

## Results at a glance

| Item | Value |
|---|---|
| Customers / features | 200 / 5 (`CustomerID`, `Gender`, `Age`, `Annual Income`, `Spending Score`) |
| Clustering space | standardised **Annual Income + Spending Score** |
| Selected model | K-Means, **k = 5** (elbow, silhouette and Davies–Bouldin agree; Calinski–Harabasz is secondary) |
| Silhouette / DB / CH | **0.555** / 0.572 / 248.6 |
| Bootstrap stability | **ARI 0.979 ± 0.025** (30 resamples) |
| Algorithm agreement | Ward ARI 0.942, Gaussian mixture ARI 0.957, DBSCAN ARI 0.273 |
| Segment assignment | RBF SVM, **97.5%** cross-validated accuracy (**93.3%** on a 70/30 hold-out) |

### The five segments

| Segment | n | Share | Age | Income (k$) | Spending | % Female |
|---|---|---|---|---|---|---|
| C0 Frugal | 23 | 11.5% | 45.2 ± 13.2 | 26.3 ± 7.9 | 20.9 ± 13.0 | 61 |
| C1 Impulsive | 22 | 11.0% | 25.3 ± 5.3 | 25.7 ± 7.6 | 79.4 ± 10.5 | 59 |
| C2 Standard | 81 | 40.5% | 42.7 ± 16.5 | 55.3 ± 9.0 | 49.5 ± 6.5 | 59 |
| C3 Conservative | 35 | 17.5% | 41.1 ± 11.3 | 88.2 ± 16.4 | 17.1 ± 10.0 | 46 |
| C4 Target | 39 | 19.5% | 32.7 ± 3.7 | 86.5 ± 16.3 | 82.1 ± 9.4 | 54 |

Reading of the segments:

- **Target** — high income, high spend, and the youngest group (33 ± 4 years). Protect with loyalty tiers and early access.
- **Conservative** — the *highest* income but the *lowest* spending: the biggest untapped value pool. Reactivate with premium assortment, not discounts.
- **Impulsive** — young (25 ± 5) and spending far beyond their income. Trends, social media and instalments beat price cuts.
- **Frugal** — older, low income, low spend. Value packs, coupons, essentials.
- **Standard** — 40% of the base. Retention and cross-selling; small per-customer gains matter most here.

---

## Repository layout

```
Mall_Customers.csv          # raw dataset (200 x 5)
src/common.py               # paths, plotting style, data loading
src/01_eda.py               # data quality, distributions, correlations, gender tests
src/02_clustering.py        # k selection, K-Means, 4 alternative algorithms, profiles
src/03_classification.py    # 6 classifiers, CV + hold-out, confusion, importances
figures/                    # fig1 ... fig13 (300 dpi, generated)
results/                    # every number in the report, as CSV / JSON
report/report.html          # ICML-style source (two columns, 10 pt Times)
report/report.pdf           # 9-page submission version (print-ready)
report/report.docx          # same layout in Word (8 pages, editable, full-width tables)
slides/Mall_Customer_Segmentation.pptx   # 12-slide deck for the 4-5 minute talk
slides/DESIGN.md            # deck design spec (palette, type scale, page plan)
```

---

## How to run

```bash
pip install -r requirements.txt      # numpy, pandas, scikit-learn, matplotlib, seaborn, scipy

python src/01_eda.py                 # EDA -> figures/fig1..fig4, results/*.csv
python src/02_clustering.py          # clustering -> fig5..fig8, fig13, results/segments.csv
python src/03_classification.py      # classifiers -> fig9..fig12
```

The scripts are independent: `02` only needs the raw CSV, `03` reads `results/segments.csv` produced by `02`. Everything is seeded with `random_state=42`; the full pipeline runs in a few seconds on a laptop CPU.

To regenerate the PDF report from the HTML source (Windows, Edge or Chrome headless):

```bash
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" ^
  --headless=new --disable-gpu --no-pdf-header-footer ^
  --print-to-pdf="report/report.pdf" ^
  "file:///C:/path/to/report/report.html"
```

---

## Method summary

1. **EDA** — no missing values or duplicates; income and spending are uncorrelated (*r* = 0.01), age correlates negatively with spending (*r* = −0.33); gender shows no significant difference (Welch *t*-test, *p* > 0.40, confirmed by Mann–Whitney).
2. **Feature space** — income + spending, z-scored. Adding age *lowers* the silhouette from 0.555 to 0.417, so age is kept as a descriptive variable instead.
3. **Model selection** — four internal indices over k = 2…10. Elbow, silhouette (0.555) and Davies–Bouldin (0.572) select k = 5; Calinski–Harabasz peaks at k = 9 and is treated as secondary because it rewards finer partitions.
4. **Validation** — 30 bootstrap resamples (ARI 0.979) and four alternative algorithms; DBSCAN fails because the groups are separated by gaps of varying width, not by uniform low-density regions.
5. **Assignment** — six classifiers reproduce the segmentation from a customer profile. The best is an RBF SVM at 97.5% CV accuracy. Because the labels are derived from two of the inputs, this accuracy is partly circular; a **demographics-only** baseline reaches 40.0%, i.e. the majority-class rate, and is reported as the honest limit.

---

## Notes and limitations

- The dataset is small (200 records) and the "spending score" is an opaque mall-assigned summary, not revenue; the segmentation is cross-sectional, with no recency or frequency information.
- `k = 5` is well supported but remains a modelling choice: k = 6 is only marginally worse on silhouette and would split the affluent high-spending Target segment.
- The classifier is a **deployment convenience** (a cheap routing rule), not evidence that segment membership is predictable from demographics.

## References

Foundational sources: MacQueen (1967); Hartigan & Wong (1979); Rousseeuw (1987); Davies & Bouldin (1979); Hubert & Arabie (1985); Ward (1963); Ester et al. (1996); Cortes & Vapnik (1995); Breiman (2001); Pedregosa et al. (2011); Punj & Stewart (1983); Wedel & Kamakura (2000).

Recent work: John, Shobayo & Ogunleye (2023, *Analytics*, [doi:10.3390/analytics2040042](https://doi.org/10.3390/analytics2040042)) compared five clustering algorithms on retail RFM data; Kuo, Alfareza & Nguyen (2023, *JESTCH*, [doi:10.1016/j.jestch.2023.101525](https://doi.org/10.1016/j.jestch.2023.101525)) improved customer segmentation with density peaks and a genetic algorithm using ARI/NMI validation; Hamidi & Haghi (2024, *CHBR*, [doi:10.1016/j.chbr.2024.100520](https://doi.org/10.1016/j.chbr.2024.100520)) showed that time-series segmentation can outperform static snapshots. Full bibliography in `report/report.pdf`.

Dataset: [Mall Customer Segmentation Data](https://www.kaggle.com/datasets/vjchoudhary7/customer-segmentation-tutorial-in-python) (Kaggle).
