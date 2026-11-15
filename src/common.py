"""Shared helpers: paths, plotting style, data loading."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Mall_Customers.csv"
FIG = ROOT / "figures"
RES = ROOT / "results"
FIG.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)

# ICML-like look: serif fonts, small type, thin spines, no grid
PALETTE = ["#3B6EA5", "#E08A3C", "#4E9A51", "#C0504D", "#7B6AA8", "#4BACC6"]
GENDER_COLORS = {"Male": "#3B6EA5", "Female": "#C0504D"}


def set_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "lines.linewidth": 1.2,
    })


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df = df.rename(columns={
        "Annual Income (k$)": "Income",
        "Spending Score (1-100)": "Spending",
    })
    return df


def save(fig, name):
    path = FIG / name
    fig.savefig(path)
    plt.close(fig)
    print(f"[fig] {path.name}")


def dump(obj, name):
    path = RES / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    print(f"[res] {path.name}")
