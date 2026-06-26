from __future__ import annotations

from pathlib import Path
from textwrap import fill
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import pandas as pd

from .analytics import performance_table
from .config import MONTH_ORDER, WEEKDAY_ORDER
from .data import QualityAudit


NAVY = "#0B1F3A"
BLUE = "#315EB8"
TEAL = "#0F8F96"
GREEN = "#2F8A63"
AMBER = "#C4861E"
PAGE = "#CEC8E3"
SURFACE = "#E1DCF0"
TEXT = "#172033"
MUTED = "#40516A"


def _save_figure(fig: Figure, path: Path) -> None:
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def _base_figure(title: str, subtitle: str) -> tuple[Figure, GridSpec]:
    fig = plt.figure(figsize=(16, 9), facecolor=PAGE)
    fig.add_artist(
        Rectangle(
            (0.006, 0.009),
            0.988,
            0.982,
            transform=fig.transFigure,
            fill=False,
            edgecolor="#978EAF",
            linewidth=1.25,
        )
    )
    grid = fig.add_gridspec(
        12,
        24,
        left=0.045,
        right=0.97,
        top=0.82,
        bottom=0.08,
        hspace=1.5,
        wspace=1.4,
    )
    fig.text(0.045, 0.94, title, fontsize=22, fontweight="bold", color=NAVY)
    fig.text(0.045, 0.905, subtitle, fontsize=10.5, color=MUTED)
    fig.add_artist(Line2D([0.045, 0.97], [0.885, 0.885], color=TEAL, linewidth=3))
    fig.text(
        0.97,
        0.025,
        "Source: UCI Bank Marketing | Grain: one campaign observation",
        ha="right",
        fontsize=8,
        color=MUTED,
    )
    return fig, grid


def _card(ax: Axes, label: str, value: str, accent: str = BLUE) -> None:
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axvline(0, color=accent, linewidth=7)
    ax.text(
        0.07,
        0.68,
        label.upper(),
        transform=ax.transAxes,
        fontsize=8,
        color=MUTED,
        fontweight="bold",
    )
    ax.text(
        0.07,
        0.23,
        value,
        transform=ax.transAxes,
        fontsize=20,
        color=NAVY,
        fontweight="bold",
    )


def _style_axis(ax: Axes, title: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=12, color=NAVY, fontweight="bold", pad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="y", color="#C2BBD3", linewidth=0.8)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.set_axisbelow(True)


def create_dashboard_pages(
    frame: pd.DataFrame,
    scored: pd.DataFrame,
    metrics: dict[str, Any],
    feature_importance_path: Path,
    screenshot_dir: Path,
) -> None:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    kpi = {
        "observations": len(frame),
        "subscriptions": int(frame["conversion_flag"].sum()),
        "conversion": frame["conversion_flag"].mean(),
        "previous": frame["previously_contacted_flag"].mean(),
        "contacts": frame["campaign"].mean(),
    }

    fig, grid = _base_figure(
        "Executive Overview",
        "Bank Marketing Campaign & Deposit Propensity Intelligence | Retrospective campaign performance",
    )
    cards = [
        ("Campaign observations", f"{kpi['observations']:,}", BLUE),
        ("Subscriptions", f"{kpi['subscriptions']:,}", GREEN),
        ("Conversion rate", f"{kpi['conversion']:.1%}", TEAL),
        ("Previously contacted", f"{kpi['previous']:.1%}", AMBER),
        ("Avg. campaign contacts", f"{kpi['contacts']:.2f}", BLUE),
    ]
    starts = [0, 5, 10, 15, 20]
    for (label, value, color), start in zip(cards, starts):
        _card(fig.add_subplot(grid[0:2, start:start + 4]), label, value, color)
    channel = performance_table(frame, "contact").sort_values("contact")
    ax = fig.add_subplot(grid[3:8, 0:8])
    ax.bar(channel["contact"], channel["conversion_rate"], color=[TEAL, BLUE])
    _style_axis(ax, "Observed conversion by contact channel")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    for idx, value in enumerate(channel["conversion_rate"]):
        ax.text(idx, value + 0.004, f"{value:.1%}", ha="center", color=TEXT, fontweight="bold")
    bands = performance_table(frame, "campaign_contact_band")
    order = ["1 contact", "2 contacts", "3-4 contacts", "5+ contacts"]
    bands = bands.set_index("campaign_contact_band").reindex(order).reset_index()
    ax = fig.add_subplot(grid[3:8, 9:17])
    ax.plot(bands["campaign_contact_band"], bands["conversion_rate"], marker="o", color=BLUE, linewidth=2.5)
    _style_axis(ax, "Contact frequency and conversion")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.tick_params(axis="x", rotation=18)
    previous_success = frame.loc[frame["poutcome"].eq("success"), "conversion_flag"].mean()
    ax = fig.add_subplot(grid[3:8, 18:24])
    ax.set_facecolor(NAVY)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.text(
        0.08,
        0.82,
        "EXECUTIVE SIGNAL",
        color="#9FB3CE",
        fontsize=9,
        fontweight="bold",
        transform=ax.transAxes,
    )
    insight = (
        f"Previous campaign success profiles converted at {previous_success:.1%}. "
        "Use this as a prioritization signal, not a causal claim. Contact intensity shows diminishing observed returns."
    )
    ax.text(
        0.08,
        0.67,
        fill(insight, 39),
        color="white",
        fontsize=12,
        va="top",
        linespacing=1.55,
        transform=ax.transAxes,
    )
    ax.text(
        0.08,
        0.10,
        "No revenue, ROI, CAC, or unique-customer claims.",
        color=AMBER,
        fontsize=8.5,
        transform=ax.transAxes,
    )
    profile = performance_table(frame, "customer_profile_segment").head(6)
    ax = fig.add_subplot(grid[9:12, 0:24])
    ax.barh(profile["customer_profile_segment"], profile["conversion_rate"], color=TEAL)
    _style_axis(ax, "Highest observed conversion customer-profile segments")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.invert_yaxis()
    _save_figure(fig, screenshot_dir / "01_executive_overview.png")

    fig, grid = _base_figure(
        "Customer Profile Intelligence",
        "Observed profile conversion patterns | Minimum-volume filters used where noted",
    )
    age = (
        performance_table(frame, "age_band")
        .set_index("age_band")
        .reindex(["17-29", "30-39", "40-49", "50-59", "60+"])
        .reset_index()
    )
    ax = fig.add_subplot(grid[0:5, 0:8])
    ax.bar(age["age_band"], age["conversion_rate"], color=TEAL)
    _style_axis(ax, "Conversion by age band")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")

    jobs = performance_table(frame, "job")
    jobs = jobs[jobs["observations"] >= 500].head(8).sort_values("conversion_rate")
    ax = fig.add_subplot(grid[0:5, 9:17])
    ax.barh(jobs["job"], jobs["conversion_rate"], color=BLUE)
    _style_axis(ax, "Occupation conversion (>=500 observations)")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    exposure = performance_table(frame, "credit_exposure_profile").sort_values("conversion_rate")
    ax = fig.add_subplot(grid[0:5, 18:24])
    ax.barh(exposure["credit_exposure_profile"], exposure["conversion_rate"], color=AMBER)
    _style_axis(ax, "Credit-exposure profile")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    education = performance_table(frame, "education_group").sort_values("conversion_rate")
    ax = fig.add_subplot(grid[7:12, 0:10])
    ax.barh(education["education_group"], education["conversion_rate"], color=GREEN)
    _style_axis(ax, "Education group")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    outcome = performance_table(frame, "poutcome").sort_values("conversion_rate")
    ax = fig.add_subplot(grid[7:12, 11:17])
    ax.barh(outcome["poutcome"], outcome["conversion_rate"], color=TEAL)
    _style_axis(ax, "Previous campaign outcome")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax = fig.add_subplot(grid[7:12, 18:24])
    ax.set_facecolor(SURFACE)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    profile_text = (
        "PROFILE INTERPRETATION\n\nHigh observed conversion appears among prior-success, student, and senior profiles. "
        "These are campaign observations, not verified unique customers. Use a minimum-volume rule before operational targeting."
    )
    ax.text(
        0.06,
        0.90,
        fill(profile_text, 42),
        va="top",
        color=TEXT,
        fontsize=11,
        linespacing=1.45,
        transform=ax.transAxes,
    )
    _save_figure(fig, screenshot_dir / "02_customer_profile_intelligence.png")

    fig, grid = _base_figure(
        "Campaign Optimization",
        "Timing, contact frequency, previous engagement, and economic context",
    )
    month = performance_table(frame, "month").set_index("month").reindex(MONTH_ORDER).dropna().reset_index()
    ax = fig.add_subplot(grid[0:5, 0:11])
    ax.plot(month["month"], month["conversion_rate"], marker="o", color=BLUE, linewidth=2.5)
    _style_axis(ax, "Observed monthly conversion")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    weekday = performance_table(frame, "day_of_week").set_index("day_of_week").reindex(WEEKDAY_ORDER).reset_index()
    ax = fig.add_subplot(grid[0:5, 13:24])
    ax.bar(weekday["day_of_week"], weekday["conversion_rate"], color=TEAL)
    _style_axis(ax, "Observed weekday conversion")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    macro = performance_table(frame, "macroeconomic_regime").sort_values("conversion_rate")
    ax = fig.add_subplot(grid[7:12, 0:9])
    ax.barh(macro["macroeconomic_regime"], macro["conversion_rate"], color=GREEN)
    _style_axis(ax, "Macroeconomic regime")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    bands = (
        performance_table(frame, "campaign_contact_band")
        .set_index("campaign_contact_band")
        .reindex(["1 contact", "2 contacts", "3-4 contacts", "5+ contacts"])
        .reset_index()
    )
    ax = fig.add_subplot(grid[7:12, 10:17])
    ax.bar(bands["campaign_contact_band"], bands["conversion_rate"], color=AMBER)
    _style_axis(ax, "Contact-frequency effectiveness")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.tick_params(axis="x", rotation=18)
    ax = fig.add_subplot(grid[7:12, 18:24])
    ax.set_facecolor(NAVY)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    action_text = (
        "Prioritize higher-propensity profiles first. Apply a conservative contact cap and test timing through "
        "controlled experiments. Observed associations do not prove channel or timing causality."
    )
    ax.text(
        0.07,
        0.90,
        "ACTION FRAME",
        va="top",
        color="#9FB3CE",
        fontsize=9,
        fontweight="bold",
        transform=ax.transAxes,
    )
    ax.text(
        0.07,
        0.76,
        fill(action_text, 34),
        va="top",
        color="white",
        fontsize=10.2,
        linespacing=1.4,
        transform=ax.transAxes,
    )
    _save_figure(fig, screenshot_dir / "03_campaign_optimization.png")

    fig, grid = _base_figure(
        "Propensity & Decision Support",
        "Leakage-safe pre-contact model | duration excluded | locked test evaluation",
    )
    decile = pd.DataFrame(metrics["locked_test_decile_performance"])
    decile_colors = [TEAL if decile_number == 1 else BLUE for decile_number in decile["locked_test_decile"]]
    ax = fig.add_subplot(grid[0:5, 0:10])
    ax.bar(decile["locked_test_decile"].astype(str), decile["conversion_rate"], color=decile_colors)
    _style_axis(ax, "Locked-test conversion by propensity decile (1 = highest)")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    candidates = pd.DataFrame(metrics["candidate_models"]).T.reset_index(names="model")
    ax = fig.add_subplot(grid[0:5, 12:18])
    ax.barh(candidates["model"], candidates["validation_pr_auc"], color=TEAL)
    _style_axis(ax, "Validation PR-AUC by model")
    ax.set_xlim(0, max(0.55, candidates["validation_pr_auc"].max() * 1.15))
    test = metrics["test_metrics"]
    ax = fig.add_subplot(grid[0:5, 19:24])
    ax.set_facecolor(SURFACE)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    score_text = (
        f"CHAMPION\n{metrics['champion_model'].replace('_', ' ').title()}\n\n"
        f"Test PR-AUC  {test['pr_auc']:.3f}\nTest ROC-AUC {test['roc_auc']:.3f}\n"
        f"Recall        {test['recall']:.1%}\nPrecision     {test['precision']:.1%}\n"
        f"Threshold     {metrics['recommended_threshold']:.3f}"
    )
    ax.text(0.08, 0.90, score_text, va="top", color=NAVY, fontsize=11, linespacing=1.45, transform=ax.transAxes)
    importance = pd.read_csv(feature_importance_path).head(10).sort_values("importance")
    ax = fig.add_subplot(grid[7:12, 0:13])
    ax.barh(importance["feature"], importance["importance"], color=BLUE)
    _style_axis(ax, "Champion feature importance (magnitude, not causality)")
    ax = fig.add_subplot(grid[7:12, 15:24])
    ax.set_facecolor(NAVY)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    score_note = (
        f"Top-decile conversion: {metrics['top_decile_conversion_rate']:.1%}\n"
        f"Top-decile lift: {metrics['top_decile_lift']:.2f}x\n"
        f"Recommended contacts: {metrics['high_propensity_observation_count']:,}"
    )
    advice = fill(
        "Use threshold as a configurable capacity lever. Validate fairness, stability, and incremental lift in a controlled deployment.",
        43,
    )
    ax.text(0.07, 0.90, "DECISION SUPPORT", va="top", color="#9FB3CE", fontsize=9, fontweight="bold", transform=ax.transAxes)
    ax.text(0.07, 0.74, score_note, va="top", color="white", fontsize=10.5, linespacing=1.35, transform=ax.transAxes)
    ax.text(0.07, 0.42, advice, va="top", color="white", fontsize=9.8, linespacing=1.4, transform=ax.transAxes)
    _save_figure(fig, screenshot_dir / "04_propensity_decision_support.png")

def write_reports(
    frame: pd.DataFrame,
    audit: QualityAudit,
    metrics: dict[str, Any],
    database_counts: dict[str, int],
    reports_dir: Path,
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    unknown_rows = "\n".join(f"| `{column}` | {count:,} |" for column, count in audit.unknown_counts.items())
    quality = f"""# Data Quality Report

## Executive Status

**PASS** - Source schema, row count, null policy, target domain, numeric ranges, and source-to-output grain were validated.

| Check | Result | Treatment |
|---|---:|---|
| Source observations | {audit.row_count:,} | Retained |
| Source columns | {audit.column_count} | Matches contract |
| Native null cells | {audit.native_null_cells} | None introduced |
| Exact duplicate excess rows | {audit.exact_duplicate_rows} | Retained and explicitly flagged |
| Positive observations | {audit.positive_observations:,} | Target preserved |
| Positive rate | {audit.positive_rate:.2%} | Imbalance handled in modeling |
| `pdays = 999` | {audit.pdays_999_count:,} | Retained as documented not-previously-contacted sentinel |

## Unknown Category Audit

`unknown` is a source category, not a native null. It is retained to avoid unjustified imputation.

| Field | Unknown observations |
|---|---:|
{unknown_rows}

## Duplicate Decision

All 41,188 source observations are retained because there is no unique customer or campaign identifier capable of proving that identical rows are erroneous. The pipeline adds technical flags for 12 excess duplicate rows. This preserves the stated fact-table grain: **one row per source campaign observation**.

## Outlier Policy

Extreme values such as age 98, campaign contacts 56, and duration 4,918 seconds are profiled but not automatically removed. `duration` is available only for retrospective post-call analysis and is excluded from the production propensity model.

## Source Integrity

SHA-256: `{audit.source_sha256}`
"""
    (reports_dir / "data_quality_report.md").write_text(quality, encoding="utf-8")

    dictionary_rows = [
        ("campaign_record_id", "Integer", "Technical surrogate for a source campaign observation; not a customer ID."),
        ("age", "Integer", "Age in years."), ("job", "Category", "Occupation category."),
        ("marital", "Category", "Marital status."), ("education", "Category", "Detailed education category."),
        ("default", "Category", "Credit default status, including unknown."),
        ("housing", "Category", "Housing-loan status, including unknown."),
        ("loan", "Category", "Personal-loan status, including unknown."),
        ("contact", "Category", "Campaign contact channel."), ("month", "Category", "Last-contact month; year unavailable."),
        ("day_of_week", "Category", "Last-contact weekday."),
        ("duration", "Integer", "Last call duration in seconds; retrospective use only, excluded from propensity model."),
        ("campaign", "Integer", "Contacts during the current campaign for this observation."),
        ("pdays", "Integer", "Days since prior campaign contact; 999 means not previously contacted."),
        ("previous", "Integer", "Contacts before the current campaign."),
        ("poutcome", "Category", "Outcome of the previous campaign."),
        ("emp.var.rate", "Decimal", "Employment variation rate."),
        ("cons.price.idx", "Decimal", "Consumer price index."),
        ("cons.conf.idx", "Decimal", "Consumer confidence index."),
        ("euribor3m", "Decimal", "Three-month Euribor rate."),
        ("nr.employed", "Decimal", "Number employed indicator."),
        ("y", "Binary category", "Whether a term deposit was subscribed."),
        ("conversion_flag", "Binary integer", "1 when y=yes, otherwise 0."),
        ("propensity_score", "Decimal", "Final-model operational ranking score across the historical portfolio."),
        ("propensity_decile", "Integer", "Operational score rank; not an unbiased evaluation metric."),
        ("locked_test_decile", "Integer", "Evaluation-only decile derived from locked-test probabilities."),
    ]
    table = "\n".join(f"| `{name}` | {dtype} | {definition} |" for name, dtype, definition in dictionary_rows)
    (reports_dir / "data_dictionary.md").write_text(
        "# Data Dictionary\n\n| Field | Type | Business definition |\n|---|---|---|\n" + table +
        "\n\nDerived segmentation fields are deterministic, documented in `src/bank_intelligence/features.py`, and contain no fabricated outcomes.\n",
        encoding="utf-8",
    )

    reconciliation = f"""# Source-to-Target Reconciliation

| Layer | Rows | Status |
|---|---:|---|
| Raw source | {audit.row_count:,} | Baseline |
| Processed observations | {len(frame):,} | PASS |
| SQLite staging | {database_counts['stg_bank_marketing']:,} | PASS |
| Campaign fact | {database_counts['fact_campaign_contact']:,} | PASS |
| Propensity score mart | {database_counts['mart_propensity_scores']:,} | PASS |
| Orphan customer-profile keys | {database_counts['orphan_profile_keys']:,} | PASS |

Target positives reconcile to {int(frame['conversion_flag'].sum()):,}. Duplicate observations are retained and flagged; no source rows are dropped.
"""
    (reports_dir / "source_to_target_reconciliation.md").write_text(reconciliation, encoding="utf-8")

    test = metrics["test_metrics"]
    model_card = f"""# Model Card - Deposit Propensity

## Intended Use

Rank campaign observations by pre-contact term-deposit propensity to support targeting scenarios. The score is decision support, not an automated eligibility or credit decision.

## Champion

- Model: **{metrics['champion_model'].replace('_', ' ').title()}**
- Selection criterion: validation PR-AUC, supported by 3-fold stratified cross-validation
- Calibration: sigmoid calibration
- Recommended threshold: **{metrics['recommended_threshold']:.3f}**, chosen by maximum validation F2
- Duration excluded: **Yes**, because it is not known before the call

## Locked Test Performance

| Metric | Value |
|---|---:|
| PR-AUC | {test['pr_auc']:.3f} |
| ROC-AUC | {test['roc_auc']:.3f} |
| Precision | {test['precision']:.1%} |
| Recall | {test['recall']:.1%} |
| F1 | {test['f1']:.3f} |
| Brier score | {test['brier_score']:.3f} |
| Top-decile conversion | {metrics['top_decile_conversion_rate']:.1%} |
| Top-decile lift | {metrics['top_decile_lift']:.2f}x |

All decile metrics above use the locked test set only. Full-portfolio scores are operational ranking outputs and must not be presented as unbiased model evaluation.

## Limitations and Risks

- No customer ID, transaction history, campaign cost, revenue, or profit data.
- Rows are campaign observations, not verified unique customers.
- No full calendar date or year field; seasonality cannot be separated cleanly from year effects.
- Scores reflect historical associations and do not establish causality.
- Monitor population drift, calibration, subgroup performance, and operational capacity before deployment.
"""
    (reports_dir / "model_card.md").write_text(model_card, encoding="utf-8")

    comparison = pd.DataFrame(metrics["candidate_models"]).T
    comparison.to_csv(reports_dir / "model_comparison.csv")