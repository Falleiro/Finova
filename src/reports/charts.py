"""
Chart generation for FINOVA reports.
Outputs PNG files to /tmp/finova_charts/ and returns the path.
"""

import logging
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — must be set before importing pyplot
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

CHARTS_DIR = Path("/tmp/finova_charts")


def _ensure_charts_dir() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)


async def build_spending_chart(by_category: dict[str, int], title: str) -> str:
    _ensure_charts_dir()
    labels = list(by_category.keys())
    values = [v / 100 for v in by_category.values()]  # cents → BRL

    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.82,
    )
    for text in autotexts:
        text.set_fontsize(9)
    ax.set_title(f"Gastos por Categoria\n{title}", fontsize=13, pad=15)

    chart_path = str(CHARTS_DIR / "spending_pie.png")
    fig.savefig(chart_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    logger.info("Chart saved to %s", chart_path)
    return chart_path


async def build_balance_bar_chart(accounts: list[dict], title: str) -> str:
    _ensure_charts_dir()
    labels = [f"{a['institution']}\n({a['type']})" for a in accounts]
    values = [a["balance_cents"] / 100 for a in accounts]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color="#4CAF50", edgecolor="white")
    ax.bar_label(bars, fmt="R$ %.2f", padding=4, fontsize=9)
    ax.set_title(f"Saldo por Conta\n{title}", fontsize=13)
    ax.set_ylabel("Saldo (R$)")
    ax.tick_params(axis="x", labelsize=9)
    fig.tight_layout()

    chart_path = str(CHARTS_DIR / "balance_bar.png")
    fig.savefig(chart_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    logger.info("Chart saved to %s", chart_path)
    return chart_path
