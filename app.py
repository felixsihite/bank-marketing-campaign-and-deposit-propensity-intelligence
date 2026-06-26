from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
NAVY = "#0B1F3A"
BLUE = "#2F6BFF"
TEAL = "#13A6A6"
GREEN = "#2EAD70"
AMBER = "#F2B84B"
MONTH_ORDER = ["mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
WEEKDAY_ORDER = ["mon", "tue", "wed", "thu", "fri"]

st.set_page_config(
    page_title="Bank Marketing Campaign & Deposit Propensity Intelligence",
    page_icon="BI",
    layout="wide",
    initial_sidebar_state="expanded",
)

NATIVE_THEME_TYPE = st.context.theme.type or "dark"
DEFAULT_MODE_INDEX = 0 if NATIVE_THEME_TYPE == "dark" else 1
DISPLAY_MODE = st.sidebar.radio(
    "Display mode",
    ["Dark", "Light"],
    index=DEFAULT_MODE_INDEX,
    horizontal=True,
    help="Switches the complete dashboard palette, including Plotly charts.",
)
IS_DARK = DISPLAY_MODE == "Dark"
PAGE_BACKGROUND = "#071A2E" if IS_DARK else "#CEC8E3"
SIDEBAR_BACKGROUND = "#0C243D" if IS_DARK else "#D8D3E8"
SURFACE = "#102A46" if IS_DARK else "#E1DCF0"
SURFACE_ALT = "#153553" if IS_DARK else "#DCD7EC"
TEXT = "#EAF2FB" if IS_DARK else "#10243D"
MUTED = "#A9BCD0" if IS_DARK else "#40516A"
BORDER = "#274763" if IS_DARK else "#978EAF"
GRID = "#294965" if IS_DARK else "#C2BBD3"

st.markdown(
    f"""
    <style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: {PAGE_BACKGROUND}; color: {TEXT}; }}
    [data-testid="stSidebar"] {{ background: {SIDEBAR_BACKGROUND}; border-right: 1px solid {BORDER}; }}
    [data-testid="stSidebar"] > div:first-child {{ background: {SIDEBAR_BACKGROUND}; }}
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stMarkdownContainer"] li,
    .stApp [data-testid="stMarkdownContainer"] strong {{ color: {TEXT}; }}
    [data-testid="stCaptionContainer"] {{ color: {MUTED} !important; }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [role="radiogroup"] p {{ color: {TEXT} !important; }}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{ background: {SURFACE_ALT} !important; border-color: {BORDER} !important; }}
    [data-testid="stSidebar"] [data-baseweb="select"] input {{ color: {TEXT} !important; caret-color: {TEXT} !important; }}
    [data-testid="stSidebar"] [data-baseweb="select"] svg {{ color: {MUTED} !important; }}
    [data-testid="stSidebar"] [data-baseweb="tag"] {{ background: {TEAL} !important; }}
    [data-testid="stSidebar"] [data-baseweb="tag"] span,
    [data-testid="stSidebar"] [data-baseweb="tag"] svg {{ color: #071A2E !important; }}
    [data-baseweb="popover"], [data-baseweb="menu"] {{ background: {SURFACE}; color: {TEXT}; }}
    [data-baseweb="menu"] li {{ color: {TEXT} !important; }}
    .hero {{ background: linear-gradient(120deg, #0B2745 0%, #123F66 100%); border: 1px solid #2B587B; border-radius: 14px; padding: 1.45rem 1.65rem; margin-bottom: 1rem; box-shadow: 0 12px 30px rgba(4, 20, 36, .18); }}
    .hero h1 {{ color: white !important; margin: 0; font-size: 2rem; }}
    .hero p {{ color: #C7D7E8 !important; margin: .45rem 0 0; }}
    .scope {{ color: {TEXT}; border-left: 5px solid {TEAL}; background: {SURFACE}; padding: .8rem 1rem; border-radius: 6px; }}
    div[data-testid="stMetric"] {{ background: {SURFACE}; border: 1px solid {BORDER}; padding: .8rem 1rem; border-radius: 10px; box-shadow: 0 5px 16px rgba(4, 20, 36, .08); }}
    div[data-testid="stMetric"] label,
    div[data-testid="stMetricLabel"] p {{ color: {MUTED} !important; }}
    div[data-testid="stMetricValue"], h1, h2, h3 {{ color: {TEXT} !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: .4rem; }}
    .stTabs [data-baseweb="tab"] {{ color: {TEXT}; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px 8px 0 0; padding: .55rem .9rem; }}
    .stTabs [data-baseweb="tab"] p {{ color: {TEXT} !important; }}
    .stTabs [aria-selected="true"] {{ border-bottom: 3px solid {TEAL}; background: {SURFACE_ALT}; }}
    [data-testid="stDataFrame"], [data-testid="stTable"] {{ border: 1px solid {BORDER}; border-radius: 10px; overflow: hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_assets() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    observations = pd.read_csv(ROOT / "data" / "processed" / "campaign_observations.csv")
    scores = pd.read_csv(ROOT / "outputs" / "predictions" / "propensity_scores.csv")
    metrics = json.loads((ROOT / "outputs" / "reports" / "model_metrics.json").read_text(encoding="utf-8"))
    governance = json.loads((ROOT / "outputs" / "reports" / "model_governance.json").read_text(encoding="utf-8"))
    locked_deciles = pd.read_csv(ROOT / "outputs" / "reports" / "locked_test_decile_performance.csv")
    subgroup = pd.read_csv(ROOT / "outputs" / "reports" / "subgroup_performance.csv")
    drift = pd.read_csv(ROOT / "outputs" / "reports" / "drift_monitoring.csv")
    return observations, scores, metrics, governance, locked_deciles, subgroup, drift


def performance(frame: pd.DataFrame, dimension: str) -> pd.DataFrame:
    return (
        frame.groupby(dimension, observed=True)["conversion_flag"]
        .agg(observations="size", subscriptions="sum", conversion_rate="mean")
        .reset_index()
    )


def style_figure(fig: go.Figure, percent_axis: bool = True, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="Arial", color=TEXT),
        title_font=dict(size=17, color=TEXT),
        legend_title_text="",
        legend=dict(font=dict(color=TEXT), title_font=dict(color=TEXT)),
        hoverlabel=dict(bgcolor=SURFACE_ALT, font_color=TEXT, bordercolor=BORDER),
    )
    axis_tick_font = dict(color=TEXT, size=12)
    axis_title_font = dict(color=TEXT, size=13)
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        tickfont=axis_tick_font,
        title_font=axis_title_font,
        linecolor=BORDER,
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickfont=axis_tick_font,
        title_font=axis_title_font,
        linecolor=BORDER,
    )
    fig.update_annotations(font_color=TEXT)
    if percent_axis:
        fig.update_yaxes(tickformat=".0%")
    return fig


observations, scores, model_metrics, governance, locked_deciles, subgroup, drift = load_assets()

st.markdown(
    """
    <div class="hero">
      <h1>Bank Marketing Campaign & Deposit Propensity Intelligence</h1>
      <p>Executive BI companion for campaign performance, customer-profile analysis, and leakage-safe decision support</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Analysis Controls")
    st.caption(f"Active palette: {DISPLAY_MODE}. The switch above updates the full dashboard and its charts.")
    selected_channels = st.multiselect("Contact channel", sorted(observations["contact"].unique()), default=sorted(observations["contact"].unique()))
    selected_months = st.multiselect("Contact month", MONTH_ORDER, default=MONTH_ORDER)
    selected_age = st.multiselect("Age band", ["17-29", "30-39", "40-49", "50-59", "60+"], default=["17-29", "30-39", "40-49", "50-59", "60+"])
    job_options = sorted(observations["job"].unique())
    selected_jobs = st.multiselect("Occupation", job_options, default=job_options)
    st.divider()
    st.caption("Filters apply to descriptive campaign pages. Locked-test model evaluation remains fixed and reproducible.")

filtered = observations[
    observations["contact"].isin(selected_channels)
    & observations["month"].isin(selected_months)
    & observations["age_band"].isin(selected_age)
    & observations["job"].isin(selected_jobs)
].copy()

if filtered.empty:
    st.error("No campaign observations match the selected filters. Reset at least one sidebar filter.")
    st.stop()

tabs = st.tabs([
    "Executive Overview",
    "Customer Profiles",
    "Campaign Optimization",
    "Propensity",
    "Governance",
    "Methodology",
])

with tabs[0]:
    total = len(filtered)
    subscriptions = int(filtered["conversion_flag"].sum())
    columns = st.columns(5)
    columns[0].metric("Campaign observations", f"{total:,}")
    columns[1].metric("Subscriptions", f"{subscriptions:,}")
    columns[2].metric("Conversion rate", f"{subscriptions / total:.1%}")
    columns[3].metric("Previously contacted", f"{filtered['previously_contacted_flag'].mean():.1%}")
    columns[4].metric("Average contacts", f"{filtered['campaign'].mean():.2f}")

    left, right = st.columns(2)
    channel = performance(filtered, "contact").sort_values("conversion_rate", ascending=False)
    fig = px.bar(channel, x="contact", y="conversion_rate", color="contact", color_discrete_sequence=[TEAL, BLUE],
                 title="Observed conversion by contact channel", hover_data={"observations": ":,"})
    left.plotly_chart(style_figure(fig), width="stretch")
    contact_order = ["1 contact", "2 contacts", "3-4 contacts", "5+ contacts"]
    contact_band = performance(filtered, "campaign_contact_band").set_index("campaign_contact_band").reindex(contact_order).dropna().reset_index()
    fig = px.line(contact_band, x="campaign_contact_band", y="conversion_rate", markers=True,
                  title="Contact frequency and observed conversion", color_discrete_sequence=[BLUE])
    right.plotly_chart(style_figure(fig), width="stretch")

    segments = performance(filtered, "customer_profile_segment")
    segments = segments[segments["observations"] >= 100].sort_values("conversion_rate", ascending=True)
    fig = px.bar(segments, x="conversion_rate", y="customer_profile_segment", orientation="h",
                 title="Customer-profile segments (minimum 100 observations)", color_discrete_sequence=[TEAL],
                 hover_data={"observations": ":,", "subscriptions": ":,"})
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(style_figure(fig, percent_axis=False, height=420), width="stretch")
    st.markdown('<div class="scope"><b>Interpretation:</b> these are campaign observations and profile patterns, not verified unique customers or causal effects.</div>', unsafe_allow_html=True)

with tabs[1]:
    left, right = st.columns(2)
    age = performance(filtered, "age_band").set_index("age_band").reindex(["17-29", "30-39", "40-49", "50-59", "60+"]).dropna().reset_index()
    fig = px.bar(age, x="age_band", y="conversion_rate", title="Conversion by age band", color_discrete_sequence=[TEAL])
    left.plotly_chart(style_figure(fig), width="stretch")
    jobs = performance(filtered, "job")
    jobs = jobs[jobs["observations"] >= 200].sort_values("conversion_rate")
    fig = px.bar(jobs, x="conversion_rate", y="job", orientation="h", title="Occupation conversion (minimum 200 observations)",
                 color_discrete_sequence=[BLUE], hover_data={"observations": ":,"})
    fig.update_xaxes(tickformat=".0%")
    right.plotly_chart(style_figure(fig, percent_axis=False), width="stretch")
    left, right = st.columns(2)
    exposure = performance(filtered, "credit_exposure_profile").sort_values("conversion_rate")
    fig = px.bar(exposure, x="conversion_rate", y="credit_exposure_profile", orientation="h",
                 title="Credit-exposure profile", color_discrete_sequence=[AMBER])
    fig.update_xaxes(tickformat=".0%")
    left.plotly_chart(style_figure(fig, percent_axis=False), width="stretch")
    outcome = performance(filtered, "poutcome").sort_values("conversion_rate")
    fig = px.bar(outcome, x="conversion_rate", y="poutcome", orientation="h",
                 title="Previous campaign outcome", color_discrete_sequence=[GREEN])
    fig.update_xaxes(tickformat=".0%")
    right.plotly_chart(style_figure(fig, percent_axis=False), width="stretch")

with tabs[2]:
    left, right = st.columns(2)
    month = performance(filtered, "month").set_index("month").reindex(MONTH_ORDER).dropna().reset_index()
    fig = px.line(month, x="month", y="conversion_rate", markers=True, title="Observed monthly conversion",
                  color_discrete_sequence=[BLUE], hover_data={"observations": ":,"})
    left.plotly_chart(style_figure(fig), width="stretch")
    weekday = performance(filtered, "day_of_week").set_index("day_of_week").reindex(WEEKDAY_ORDER).dropna().reset_index()
    fig = px.bar(weekday, x="day_of_week", y="conversion_rate", title="Observed weekday conversion",
                 color_discrete_sequence=[TEAL])
    right.plotly_chart(style_figure(fig), width="stretch")
    macro = performance(filtered, "macroeconomic_regime").sort_values("conversion_rate")
    fig = px.bar(macro, x="conversion_rate", y="macroeconomic_regime", orientation="h",
                 title="Conversion by macroeconomic regime", color_discrete_sequence=[GREEN],
                 hover_data={"observations": ":,"})
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(style_figure(fig, percent_axis=False), width="stretch")
    st.warning("Month and macroeconomic associations are descriptive. The source lacks complete dates and years, so these are not stable seasonality or causal estimates.")

with tabs[3]:
    test = model_metrics["test_metrics"]
    columns = st.columns(5)
    columns[0].metric("Champion", model_metrics["champion_model"].replace("_", " ").title())
    columns[1].metric("Locked-test PR-AUC", f"{test['pr_auc']:.3f}")
    columns[2].metric("Locked-test ROC-AUC", f"{test['roc_auc']:.3f}")
    columns[3].metric("Locked-test recall", f"{test['recall']:.1%}")
    columns[4].metric("Top-decile lift", f"{model_metrics['top_decile_lift']:.2f}x")

    left, right = st.columns(2)
    fig = px.bar(locked_deciles, x="locked_test_decile", y="conversion_rate",
                 title="Locked-test conversion by propensity decile", color="conversion_rate",
                 color_continuous_scale=["#D9E4FF", TEAL], hover_data={"observations": ":,", "subscriptions": ":,"})
    fig.update_layout(coloraxis_showscale=False)
    left.plotly_chart(style_figure(fig), width="stretch")

    comparison = pd.DataFrame(model_metrics["candidate_models"]).T.reset_index(names="model")
    fig = px.bar(comparison, x="validation_pr_auc", y="model", orientation="h",
                 title="Validation PR-AUC by model", color_discrete_sequence=[TEAL])
    fig.update_xaxes(tickformat=".3f")
    right.plotly_chart(style_figure(fig, percent_axis=False), width="stretch")

    score_view = scores.merge(observations[["campaign_record_id", "customer_profile_segment"]], on="campaign_record_id")
    threshold = st.slider("Operational scoring threshold", min_value=0.05, max_value=0.80,
                          value=float(round(model_metrics["recommended_threshold"], 2)), step=0.01)
    selected = score_view[score_view["propensity_score"] >= threshold]
    columns = st.columns(3)
    columns[0].metric("Operationally selected observations", f"{len(selected):,}")
    columns[1].metric("Share of scored portfolio", f"{len(selected) / len(score_view):.1%}")
    columns[2].metric("Observed conversion in selection", f"{selected['conversion_flag'].mean():.1%}" if len(selected) else "N/A")
    st.caption("Operational scenario uses final-model scores across the historical portfolio. It is not an unbiased test metric or an estimate of incremental campaign impact.")

with tabs[4]:
    columns = st.columns(4)
    columns[0].metric("Evaluation observations", f"{governance['locked_test_observations']:,}")
    columns[1].metric("Calibration error", f"{governance['expected_calibration_error']:.3f}")
    columns[2].metric("Maximum PSI", f"{governance['max_psi']:.3f}")
    columns[3].metric("Drift status", governance["drift_status"].title())
    left, right = st.columns(2)
    drift_plot = drift.sort_values("psi", ascending=True)
    fig = px.bar(drift_plot, x="psi", y="feature", orientation="h", color="status",
                 color_discrete_map={"stable": GREEN, "moderate": AMBER, "high": "#D95C5C"},
                 title="Train-to-locked-test population stability index")
    left.plotly_chart(style_figure(fig, percent_axis=False), width="stretch")
    dimension = str(right.selectbox("Subgroup dimension", sorted(subgroup["dimension"].unique())))
    dimension_mask = subgroup["dimension"].eq(dimension)
    volume_mask = subgroup["minimum_volume_pass"].astype(bool)
    subgroup_view = subgroup.loc[dimension_mask & volume_mask].copy()
    fig = px.scatter(subgroup_view, x="recall", y="precision", size="observations", color="member",
                     title="Locked-test subgroup precision and recall", hover_data={"observations": ":,"})
    fig.update_xaxes(tickformat=".0%")
    fig.update_yaxes(tickformat=".0%")
    right.plotly_chart(style_figure(fig, percent_axis=False), width="stretch")
    st.info(governance["protected_attribute_note"])
    st.dataframe(subgroup_view[["member", "observations", "base_rate", "precision", "recall", "brier_score"]],
                 hide_index=True, width="stretch", column_config={
                     "base_rate": st.column_config.NumberColumn(format="percent"),
                     "precision": st.column_config.NumberColumn(format="percent"),
                     "recall": st.column_config.NumberColumn(format="percent"),
                 })

with tabs[5]:
    st.subheader("Analytical Contract")
    st.markdown(
        """
        - **Fact grain:** one source campaign observation; `campaign_record_id` is not a customer ID.
        - **Target:** observed term-deposit subscription (`y`).
        - **Leakage control:** post-call `duration` is excluded from production propensity features.
        - **Evaluation:** model selection uses validation PR-AUC; headline performance and decile lift use the locked test set only.
        - **Operational scoring:** final-model scores across all historical rows support ranking demonstrations, not unbiased evaluation.
        - **Unsupported claims:** no revenue, ROI, CAC, CLV, retention, churn, or unique-customer metrics.
        """
    )
    st.subheader("Locked-Test Model Metrics")
    st.json(test, expanded=False)
    st.subheader("Download Filtered Descriptive Data")
    st.download_button(
        "Download selected campaign observations (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="selected_campaign_observations.csv",
        mime="text/csv",
    )